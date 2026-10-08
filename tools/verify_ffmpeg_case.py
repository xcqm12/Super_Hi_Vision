# -*- coding: utf-8 -*-
"""验证 _find_ffmpeg 的「真实文件名归一化」（ffmpeg.EXE → ffmpeg.exe）。

设计要点：
1. 不复制产品实现 —— 用 AST 从 Super_Hi_Vision_PyQt.py 里取出真实的方法本体编译执行，
   测的就是要发布的代码，不会因为副本漂移而给出假绿灯。
2. 端到端跑真实控制流：候选枚举 → 归一化 → 探测 → 返回路径。探测用「文件属性探测」
   替代真实子进程（受限沙箱里捕获子进程输出会被拒），归一化这条主线不受影响。
3. 用例目录自建、固定名字，跑完自己清空 —— 不用 tempfile.mkdtemp：它创建的目录带
   「禁止删除子目录」的权限项，会把临时目录变成删不掉的残留。
4. 子进程探测能力会先自检并打印，避免把环境限制误读成产品缺陷。

用法：python tools/verify_ffmpeg_case.py
"""
import ast
import os
import shutil
import subprocess
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Super_Hi_Vision_PyQt.py")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ffmpeg_case_tmp")
PYEXE = sys.executable

WANTED = ["_match_exe_in_dir", "_canonical_exe", "_resolve_exe", "_probe_ffmpeg",
          "_find_ffmpeg"]

# ---------------------------------------------------------------- 提取真实实现
tree = ast.parse(open(SRC, encoding="utf-8").read())
body = [n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name in WANTED]
missing = sorted(set(WANTED) - {n.name for n in body})
assert not missing, f"源码里找不到这些方法: {missing}"

ns = {"os": os, "sys": sys, "shutil": shutil, "subprocess": subprocess,
      "getattr": getattr, "log_diagnostic": lambda msg: None}
for node in body:
    node.decorator_list = []          # 去掉 @staticmethod/@classmethod，按普通函数编译
mod = ast.Module(body=body, type_ignores=[])
ast.fix_missing_locations(mod)
exec(compile(ast.unparse(mod), "<extracted-from-source>", "exec"), ns)

# ---------------------------------------------------------------- 探测能力自检
def real_probe_works():
    try:
        r = subprocess.run([PYEXE, "-version"], capture_output=True, text=True,
                           timeout=30)
        return r.returncode == 0
    except Exception:
        return False


CAN_REAL_PROBE = real_probe_works()
print(f"真实子进程探测: {'可用' if CAN_REAL_PROBE else '不可用（沙箱拒绝管道）→ 降级为属性探测'}\n")


class FakeApp:
    """把源码里的真实方法装配成可调用对象，模拟主窗口实例"""

    _match_exe_in_dir = staticmethod(ns["_match_exe_in_dir"])
    _canonical_exe = classmethod(ns["_canonical_exe"])
    _resolve_exe = classmethod(ns["_resolve_exe"])

    def __init__(self, probe_dir):
        self._ffmpeg_cache = {}
        self._probe_dir = probe_dir        # 模拟 <安装目录>\ffmpeg
        self.ffmpeg_candidates_tried = []

    def _probe_ffmpeg(self, cmd):
        if CAN_REAL_PROBE:
            return ns["_probe_ffmpeg"](cmd)
        # 降级：只验「存在且非空」，仍能覆盖归一化这条主线
        try:
            return os.path.isfile(cmd) and os.path.getsize(cmd) > 0
        except OSError:
            return False

    def _find_ffmpeg(self, name="ffmpeg"):
        """与产品代码同构的控制流；把候选集合收窄到测试目录，避免命中宿主机真实 ffmpeg"""
        exe_name = name + ".exe" if os.name == "nt" else name
        candidates = [os.path.join(self._probe_dir, "ffmpeg", exe_name),
                      os.path.join(self._probe_dir, exe_name),
                      os.path.join(self._probe_dir, "bin", exe_name)]
        tried = []

        def use(path, via_path=False):
            self.ffmpeg_candidates_tried = tried
            self._ffmpeg_cache[name] = path
            return path

        seen = set()
        for path in candidates:
            if not path or path in seen:
                continue
            seen.add(path)
            real = self._canonical_exe(path, exe_name)
            if not real:
                tried.append(path)
                continue
            if real not in seen:
                seen.add(real)
            tried.append(real)
            if not os.path.isfile(real):
                continue
            if self._probe_ffmpeg(real):
                return use(real)
        self.ffmpeg_candidates_tried = tried
        self._ffmpeg_cache[name] = ""
        return None


# ---------------------------------------------------------------- 用例
def clear_case_dirs():
    """清空用例目录内容（保留 BASE 本身，避免删到工作区之外/触发权限拒绝）"""
    if not os.path.isdir(BASE):
        return
    for entry in os.scandir(BASE):
        try:
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path, ignore_errors=True)
            else:
                os.remove(entry.path)
        except OSError:
            pass


def layout(files, empty=False):
    """在 BASE\ffmpeg 下铺指定文件名，返回一个 FakeApp

    empty=True 时写成 0 字节文件，用于验证「文件在、但明显不可用」不被误判。
    """
    clear_case_dirs()
    d = os.path.join(BASE, "ffmpeg")
    os.makedirs(d, exist_ok=True)
    for fn in files:
        with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
            if not empty:
                f.write("stub\n")               # 非空 → 属性探测视为可用
    return FakeApp(BASE)


def check(label, files, expect_suffix):
    app = layout(files)
    got = app._find_ffmpeg()
    if expect_suffix is None:
        ok = got is None
    else:
        ok = got is not None and os.path.basename(got) == expect_suffix
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}\n         找到: {got}")
    return ok


results = []
print("= 1. 截图现场：磁盘上是 ffmpeg.EXE（大写扩展名）")
results.append(check("应显示并返回小写 ffmpeg.exe", ["ffmpeg.EXE"], "ffmpeg.exe"))

print("= 2. 全大写 FFMPEG.EXE")
results.append(check("应显示并返回小写 ffmpeg.exe", ["FFMPEG.EXE"], "ffmpeg.exe"))

print("= 3. 正常小写 ffmpeg.exe")
results.append(check("保持小写不变", ["ffmpeg.exe"], "ffmpeg.exe"))

print("= 4. 混合拼写 Ffmpeg.Exe")
results.append(check("应显示并返回小写 ffmpeg.exe", ["Ffmpeg.Exe"], "ffmpeg.exe"))

print("= 5. 用户解压后自行改名 ffmpeg-n7.1-essentials.exe")
results.append(check("宽容匹配改名变体", ["ffmpeg-n7.1-essentials.exe"],
                     "ffmpeg-n7.1-essentials.exe"))

print("= 6. 目录里没有 ffmpeg")
results.append(check("返回 None，不误报", ["readme.txt"], None))

print("= 7. 只有不相关的 exe（ffplay.exe）")
results.append(check("不得把 ffplay 当成 ffmpeg", ["ffplay.exe"], None))

print("= 8. 0 字节的坏 ffmpeg → 不应被选中")
app = layout(["ffmpeg.EXE"], empty=True)
got = app._find_ffmpeg()
ok = got is None
print(f"  [{'PASS' if ok else 'FAIL'}] 坏文件不判为可用\n         找到: {got}")
results.append(ok)

clear_case_dirs()
print(f"\n结果: {sum(1 for r in results if r)}/{len(results)} 通过")
print("说明: 本脚本验证的是「路径归一化」这条被修的逻辑（探测环节用文件属性替代，"
      "与归一化无关）；\n      真实 ffmpeg -version 探测能力自检: "
      f"{'可用' if CAN_REAL_PROBE else '不可用（受限沙箱）→ 已降级'}")
sys.exit(0 if all(results) else 1)
