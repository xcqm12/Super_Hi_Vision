# 代码签名说明（Code Signing）

Windows 对**未签名**的 exe 会在 UAC 提示里显示「未知发布者」，SmartScreen 也可能拦截。
本文说明本项目怎么签名、能做到什么、做不到什么。

---

## 先看这个：两种签名的效果差别

| | **自签名证书**（本项目已做） | **商业 CA 证书（OV / EV）** |
| --- | --- | --- |
| 成本 | 免费 | 约数百 ~ 数千元 / 年 |
| **你这台机器** | 不再显示「未知发布者」 | 不再显示 |
| **别人下载后** | **仍然显示「未知发布者」**（他们机器上没有这张证书） | 不再显示 |
| 适用 | 本机自用 / 内部测试 | 正式对外分发 |

> **一句话**：自签名解决的是「你自己机器上的观感」。想让所有下载者都不看到警告，
> 必须买商业证书（买完直接用下面的脚本，不用改代码）。

---

## 本机：生成证书 + 签名

```powershell
# 1) 生成 SevenZeroMeowTeam 自签名证书，并登记为本机受信任发行者（需要管理员）
powershell -ExecutionPolicy Bypass -File tools\create_signing_cert.ps1

# 只想给当前用户生效、不提权的话：
powershell -ExecutionPolicy Bypass -File tools\create_signing_cert.ps1 -TrustScope User

# 2) 给已构建好的 exe 签名（可一次给多个）
powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 `
    -Path SuperHiVision_v1.5.25.exe, SuperHiVision_Setup_v1.5.25.exe
```

生成在 `build\signing\`（已被 `.gitignore` 忽略）：

| 文件 | 说明 |
| --- | --- |
| `SevenZeroMeowTeam.cer` | 公钥，可以分发 |
| `SevenZeroMeowTeam.pfx` | **私钥，务必离线备份**；丢了就得重新签所有包 |
| `pfx-password.txt` | pfx 口令 |

签名时每个文件会先备份成 `<文件名>.unsigned`（如 `SuperHiVision_v1.5.25.exe.unsigned`），
签名只是往文件末尾追加签名数据，**不改动程序本身**，但文件哈希会变。

### 签名工具：优先微软的 signtool.exe，没有 SDK 就自动回退

`tools\sign_binaries.ps1` 会自动挑一个后端，**两者产出的签名完全等价**：

| 优先级 | 后端 | 什么时候用 |
| --- | --- | --- |
| 1 | **`signtool.exe`**（Windows SDK） | 机器上装了 SDK 就用它 —— 它也是唯一能驱动 **EV 硬件 token** 的工具 |
| 2 | **PowerShell `Set-AuthenticodeSignature`** | 没装 SDK 时自动回退；Windows 自带，不用额外安装 |

`signtool.exe` 的查找顺序：`PATH` → `Windows Kits\10\bin\<版本>\x64`（取最新版本）→ `Windows Kits\10\bin\x64` → `App Certification Kit`。

想强制指定后端或路径：

```powershell
# 只允许 signtool；找不到就报错退出（不静默回退）
... -SignMethod Signtool

# 只走 PowerShell（机器上没有 SDK 时用）
... -SignMethod PowerShell

# 显式指定某个 signtool.exe
... -SigntoolPath "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
```

无论用哪个后端，脚本都会：
1. 打印**实际执行的命令行**（`call : ...`，出问题可直接复制去手工排查）；
2. 用 `Get-AuthenticodeSignature` **复核签名结果**（不依赖退出码）；
3. 带时间戳签名失败时，自动退回不带时间戳再签一次。

`signtool` 的等效手工命令是：

```powershell
& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe" sign `
    /sha1 <证书指纹> /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 <文件>
```

### 验证

```powershell
Get-AuthenticodeSignature .\SuperHiVision_v1.5.25.exe |
    Format-List Status, SignerCertificate, TimeStamperCertificate
```

期望：`Status = Valid`，签名者为 `CN=SevenZeroMeowTeam`，且带时间戳
（有时间戳 = 证书过期后旧签名仍然有效）。

---

## 回滚

```powershell
# 恢复到签名前的文件
Move-Item .\SuperHiVision_v1.5.25.exe.unsigned .\SuperHiVision_v1.5.25.exe -Force

# 彻底移除这张证书（不再信任、UAC 不再显示该发布者）
Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -eq 'CN=SevenZeroMeowTeam' } | Remove-Item
Get-ChildItem Cert:\LocalMachine\Root, Cert:\LocalMachine\TrustedPublisher |
    Where-Object { $_.Subject -eq 'CN=SevenZeroMeowTeam' } | Remove-Item
```

---

## CI：让 GitHub Actions 自动签名

1. 把私钥转成 base64：

   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes('build\signing\SevenZeroMeowTeam.pfx')) |
       Set-Clipboard
   ```

2. 仓库 → **Settings → Secrets and variables → Actions** 添加两个 secret：

   | Secret | 值 |
   | --- | --- |
   | `SIGNING_PFX_BASE64` | 上面复制的那串 base64 |
   | `SIGNING_PFX_PASSWORD` | pfx 口令 |

3. 之后推 `v*` tag 时，workflow 会：导入证书 → 签名绿色版 exe → 打 NSIS 包 → 签名安装包。

**没配这两个 secret 时，签名步骤自动跳过**，构建照常出包、不会失败。

---

## exe 属性里的「发行者」：版本信息资源

除了数字签名，exe / 安装包的**属性 → 详细信息**里也会显示发行者，这部分**不需要证书**，
重新打包即生效，已固定在构建配置里：

- `SuperHiVision.spec` — 动态生成 PyInstaller 版本资源；
  版本号从 `Super_Hi_Vision_PyQt.py` 的 `__version__` 读取，**不用两处维护**
- `installer.nsi` — `VIProductVersion` + `VIAddVersionKey`（CompanyName = SevenZeroMeowTeam）

---

## 换成商业证书

买到 OV/EV 代码签名证书（拿到 `.pfx`，或硬件 token）后：

```powershell
# 本地
powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 -Path <exe> -Thumbprint <新证书指纹>
```

CI 则把新的 pfx 覆盖到那两个 secret 即可 —— 脚本按指纹/主题自动挑选证书，**代码不用改**。

> 注意：EV 证书通常要求**硬件 token**，CI 里没法直接用 pfx，那种情况一般要上云签名服务
> （如 Azure Trusted Signing）。本地插着 EV token 时，脚本已经会**优先调用 `signtool.exe`**
> —— token 的 `/csp` / `/kc` 参数就是加在这个调用上，必要时用 `-SignMethod Signtool` 强制走它。
