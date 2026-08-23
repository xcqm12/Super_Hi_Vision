import os
import sys
import subprocess
import platform
import tempfile
import shutil

# 国内镜像源列表
MIRROR_SOURCES = [
    {
        "name": "清华源",
        "url": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "trusted_host": "pypi.tuna.tsinghua.edu.cn"
    },
    {
        "name": "阿里源", 
        "url": "https://mirrors.aliyun.com/pypi/simple/",
        "trusted_host": "mirrors.aliyun.com"
    },
    {
        "name": "华为源",
        "url": "https://repo.huaweicloud.com/repository/pypi/simple/", 
        "trusted_host": "repo.huaweicloud.com"
    },
    {
        "name": "腾讯源",
        "url": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "trusted_host": "mirrors.cloud.tencent.com"
    }
]

def check_python_version():
    """检查Python版本"""
    import sys
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python版本: {sys.version}")
        return True
    else:
        print(f"❌ Python版本过低: {sys.version}，需要3.7+")
        return False

def check_package(package_name, import_name=None):
    """检查包是否安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False

def install_package(package_name):
    """使用国内源安装包"""
    print(f"正在安装 {package_name}...")
    
    for mirror in MIRROR_SOURCES:
        try:
            print(f"  尝试使用{mirror['name']}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                package_name, "-i", mirror['url'],
                "--trusted-host", mirror['trusted_host'],
                "--timeout", "60",
                "--retries", "3"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ 使用{mirror['name']}安装{package_name}成功")
                return True
            else:
                print(f"  {mirror['name']}安装失败: {result.stderr}")
        except Exception as e:
            print(f"  {mirror['name']}安装异常: {e}")
            continue
    
    # 尝试默认源
    try:
        print("尝试使用默认源安装...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ 使用默认源安装{package_name}成功")
            return True
        else:
            print(f"❌ 默认源安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 安装{package_name}异常: {e}")
        return False

def check_ffmpeg():
    """检查FFmpeg是否安装（优先检测程序自带的本地 ffmpeg 目录）"""
    # 优先检测程序自带的 ffmpeg 目录（安装包已合成）
    local_ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
    local_ffmpeg = os.path.join(local_ffmpeg_dir, "ffmpeg.exe")

    if os.path.exists(local_ffmpeg):
        # 将本地 ffmpeg 目录加入 PATH，供子进程直接调用
        os.environ["PATH"] = local_ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        print(f"✅ FFmpeg 已随程序自带: {local_ffmpeg}")
        return True

    # 其次检测系统 PATH 中的 ffmpeg
    if shutil.which("ffmpeg"):
        print("✅ FFmpeg 已安装")
        return True
    else:
        print("❌ FFmpeg 未安装")
        return False

def install_ffmpeg_windows():
    """在Windows上安装FFmpeg"""
    try:
        temp_dir = tempfile.mkdtemp()
        ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
        
        if not os.path.exists(ffmpeg_dir):
            os.makedirs(ffmpeg_dir)
        
        # 下载FFmpeg
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        print("下载FFmpeg...")
        try:
            import urllib.request
            urllib.request.urlretrieve(ffmpeg_url, zip_path)
        except:
            try:
                import requests
                response = requests.get(ffmpeg_url, stream=True)
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except:
                print("❌ FFmpeg下载失败")
                return False
        
        # 解压
        print("解压FFmpeg...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 查找并复制FFmpeg可执行文件
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(ffmpeg_dir, file)
                    shutil.copy2(src_path, dst_path)
                    print(f"✅ 复制 {file}")
        
        # 添加到PATH
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        
        # 验证安装
        try:
            result = subprocess.run([os.path.join(ffmpeg_dir, "ffmpeg.exe"), '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ FFmpeg 安装成功")
                return True
        except:
            print("❌ FFmpeg 验证失败")
            return False
            
    except Exception as e:
        print(f"❌ FFmpeg安装失败: {e}")
        return False
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def check_and_install_pyaudio():
    """检查并安装PyAudio"""
    print("\n检查PyAudio...")
    if check_package("PyAudio", "pyaudio"):
        return True
    else:
        print("尝试安装PyAudio...")
        
        # PyAudio在Windows上可能需要特殊处理
        if platform.system() == "Windows":
            return install_pyaudio_windows()
        else:
            # Linux/macOS可以直接安装
            return install_package("pyaudio")

def install_pyaudio_windows():
    """在Windows上安装PyAudio"""
    try:
        # 尝试直接安装
        if install_package("pyaudio"):
            return True
        
        # 如果直接安装失败，尝试安装预编译的wheel
        print("尝试安装预编译的PyAudio...")
        
        # 根据Python版本和系统架构选择合适的wheel
        python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
        is_64bit = platform.architecture()[0] == "64bit"
        platform_tag = "win_amd64" if is_64bit else "win32"
        
        # 尝试多个版本的wheel
        wheel_urls = [
            f"https://download.lfd.uci.edu/pythonlibs/w6tyco5e/PyAudio-0.2.13-{python_version}-{python_version}-{platform_tag}.whl",
            f"https://download.lfd.uci.edu/pythonlibs/w6tyco5e/PyAudio-0.2.12-{python_version}-{python_version}-{platform_tag}.whl",
            f"https://download.lfd.uci.edu/pythonlibs/w6tyco5e/PyAudio-0.2.11-{python_version}-{python_version}-{platform_tag}.whl",
            f"https://download.lfd.uci.edu/pythonlibs/w6tyco5e/PyAudio-0.2.11-{python_version}-none-{platform_tag}.whl"
        ]
        
        for wheel_url in wheel_urls:
            print(f"  尝试安装: {wheel_url.split('/')[-1]}")
            
            # 首先尝试直接从原始URL下载
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    wheel_url, "--timeout", "60"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print("✅ PyAudio安装成功")
                    return True
            except Exception as e:
                print(f"  直接下载失败: {e}")
            
            # 尝试使用国内源
            for mirror in MIRROR_SOURCES:
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install",
                        wheel_url, "-i", mirror['url'],
                        "--trusted-host", mirror['trusted_host'],
                        "--timeout", "60"
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        print(f"✅ 使用{mirror['name']}安装PyAudio成功")
                        return True
                except Exception as e:
                    continue
        
        print("❌ PyAudio安装失败，尝试使用 pipwin 安装...")
        
        # 尝试使用 pipwin 安装
        try:
            if install_package("pipwin"):
                result = subprocess.run([
                    sys.executable, "-m", "pipwin", "install", "pyaudio"
                ], capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    print("✅ 使用pipwin安装PyAudio成功")
                    return True
        except Exception as e:
            print(f"  pipwin安装失败: {e}")
        
        print("❌ PyAudio安装失败，可能需要手动安装")
        print("请访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
        print("下载对应版本的whl文件，然后使用 pip install 文件名.whl 安装")
        return False
        
    except Exception as e:
        print(f"❌ PyAudio安装失败: {e}")
        return False

def run_screen_recorder():
    """运行录屏程序（应用模式：优先 EXE，其次 PyQt 源码，无控制台）"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 1. 优先启动已打包的 EXE（应用模式，无控制台）
        exe_path = os.path.join(base_dir, "SuperHiVision_v1.5.10.exe")
        if os.path.exists(exe_path):
            print(f"\n✅ 启动已打包的应用: {exe_path}")
            try:
                subprocess.Popen([exe_path], cwd=base_dir)
                print("✅ 应用已启动（无控制台窗口）")
                return True
            except Exception as e:
                print(f"⚠️ 启动 EXE 失败: {e}，回退到源码运行")

        # 2. 运行 PyQt 源码（无控制台模式，pythonw 优先）
        script_path = os.path.join(base_dir, "Super_Hi_Vision_PyQt.py")
        if os.path.exists(script_path):
            print("\n" + "=" * 50)
            print("启动录屏程序（PyQt 源码）...")
            print("=" * 50)

            # 无控制台：优先 pythonw.exe
            pythonw = os.path.join(base_dir, "pythonw.exe")
            if not os.path.exists(pythonw):
                pythonw = shutil.which("pythonw.exe")
            if pythonw:
                try:
                    subprocess.Popen([pythonw, script_path], cwd=base_dir)
                    print("✅ 应用已启动（pythonw，无控制台窗口）")
                    return True
                except Exception as e:
                    print(f"⚠️ 使用 pythonw 启动失败: {e}，回退到 python 运行")

            # 回退：python.exe（可能显示控制台）
            result = subprocess.run([sys.executable, script_path], cwd=base_dir)
            if result.returncode == 0:
                print("✅ 录屏脚本执行完成")
            else:
                print("❌ 录屏脚本执行失败")
            return True
        else:
            print(f"❌ 未找到录屏程序: {script_path}")
            print("请确保 Super_Hi_Vision_PyQt.py 文件存在")
            return False

    except Exception as e:
        print(f"❌ 运行录屏脚本时出错: {e}")
        return False

def main():
    """主检测函数"""
    print("=" * 50)
    print("开始环境检测...")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    print("\n检查必要依赖包...")
    required_packages = [
        ("Pillow", "PIL"),
        ("pynput", "pynput"), 
        ("psutil", "psutil"),
        ("numpy", "numpy"),
        ("opencv-python", "cv2"),
        ("pygame", "pygame"),
        ("pyautogui", "pyautogui"),
        ("moviepy", "moviepy")
    ]
    
    missing_packages = []
    for package, import_name in required_packages:
        if not check_package(package, import_name):
            missing_packages.append((package, import_name))
    
    # 安装缺失的包
    if missing_packages:
        print(f"\n开始安装缺失的 {len(missing_packages)} 个包...")
        for package, import_name in missing_packages:
            if not install_package(package):
                print(f"❌ 无法安装 {package}，环境检测失败")
                return False
    
    # 检查并安装PyAudio
    pyaudio_installed = check_and_install_pyaudio()
    if not pyaudio_installed:
        print("⚠️ PyAudio安装失败，音频录制功能可能受限")
    
    # 检查FFmpeg
    print("\n检查FFmpeg...")
    if not check_ffmpeg():
        if platform.system() == "Windows":
            print("尝试自动安装FFmpeg...")
            if install_ffmpeg_windows():
                print("✅ FFmpeg安装成功")
            else:
                print("⚠️ FFmpeg安装失败，音频功能可能受限")
        else:
            print("⚠️ 请手动安装FFmpeg: sudo apt install ffmpeg 或 brew install ffmpeg")
    
    # 最终验证
    print("\n最终验证...")
    all_ok = True
    for package, import_name in required_packages:
        if not check_package(package, import_name):
            all_ok = False
    
    if all_ok:
        print("\n" + "=" * 50)
        print("✅ 环境检测通过！所有依赖已就绪")
        print("=" * 50)
        
        # 环境检测通过后，自动运行录屏脚本
        run_screen_recorder()
        return True
    else:
        print("\n" + "=" * 50)
        print("❌ 环境检测失败！请手动安装缺失的依赖")
        print("=" * 50)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)