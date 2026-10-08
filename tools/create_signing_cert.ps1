# =============================================================================
#  create_signing_cert.ps1 - Super Hi Vision
#
#  Creates a self-signed CODE SIGNING certificate for SevenZeroMeowTeam and
#  registers it as a trusted publisher on this machine.
#
#  Why: an unsigned exe makes Windows show "Unknown publisher" in the UAC
#  prompt (and SmartScreen). A self-signed cert that this machine trusts makes
#  the publisher name show up correctly *here*. It does NOT help on other
#  people's machines - for that you need a commercial CA certificate
#  (OV/EV). See docs/CODE_SIGNING.md.
#
#  ASCII only on purpose: Windows PowerShell 5.1 reads .ps1 as ANSI when the
#  file has no BOM, so non-ASCII text here would be mangled.
#
#  Usage:
#     powershell -ExecutionPolicy Bypass -File tools\create_signing_cert.ps1
#     powershell -ExecutionPolicy Bypass -File tools\create_signing_cert.ps1 -TrustScope User
# =============================================================================
[CmdletBinding()]
param(
    # Certificate subject / publisher name shown by Windows.
    [string] $Subject = 'CN=SevenZeroMeowTeam',

    # How long the certificate stays valid.
    [int] $ValidYears = 10,

    # Password for the exported .pfx. A random one is generated when omitted.
    [string] $PfxPassword,

    # Where the .cer / .pfx are written. Defaults to <repo>\build\signing.
    [string] $OutDir,

    # Where to register the trust entry:
    #   Machine - every user on this PC (needs an elevated shell)  [default]
    #   User    - just the signed-in user (works without elevation)
    #   None    - only create the certificate, do not register trust
    [ValidateSet('Machine', 'User', 'None')]
    [string] $TrustScope = 'Machine'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutDir) { $OutDir = Join-Path $repoRoot 'build\signing' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not $PfxPassword) {
    $buf = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buf)
    $PfxPassword = ([Convert]::ToBase64String($buf)) -replace '[+/=]', ''
}

Write-Host ''
Write-Host '=== [1/4] Create self-signed code-signing certificate ===' -ForegroundColor Cyan
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -FriendlyName "$Subject (Super Hi Vision)" `
    -CertStoreLocation 'Cert:\CurrentUser\My' `
    -KeyUsage DigitalSignature `
    -KeyAlgorithm RSA `
    -KeyLength 4096 `
    -KeyExportPolicy Exportable `
    -NotAfter (Get-Date).AddYears($ValidYears)

Write-Host "    Subject    : $($cert.Subject)"
Write-Host "    Thumbprint : $($cert.Thumbprint)"
Write-Host "    Expires    : $($cert.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "    Key usage  : Digital Signature / Code Signing"

Write-Host ''
Write-Host '=== [2/4] Export public (.cer) and private (.pfx) ===' -ForegroundColor Cyan
$cerPath = Join-Path $OutDir 'SevenZeroMeowTeam.cer'
$pfxPath = Join-Path $OutDir 'SevenZeroMeowTeam.pfx'
$pwdPath = Join-Path $OutDir 'pfx-password.txt'

Export-Certificate -Cert $cert -FilePath $cerPath -Force | Out-Null
Export-PfxCertificate -Cert $cert -FilePath $pfxPath `
    -Password (ConvertTo-SecureString -String $PfxPassword -AsPlainText -Force) -Force | Out-Null
Set-Content -Path $pwdPath -Value $PfxPassword -Encoding ASCII

Write-Host "    Public  : $cerPath"
Write-Host "    Private : $pfxPath"
Write-Host "    Password: $PfxPassword"
Write-Host "    .pfx holds the ONLY copy of the private key - keep it safe and offline." -ForegroundColor Yellow

Write-Host ''
Write-Host "=== [3/4] Register as trusted publisher (scope: $TrustScope) ===" -ForegroundColor Cyan
if ($TrustScope -eq 'None') {
    Write-Host '    skipped by request'
} else {
    $stores =
        if ($TrustScope -eq 'Machine') {
            @('Cert:\LocalMachine\Root', 'Cert:\LocalMachine\TrustedPublisher')
        } else {
            @('Cert:\CurrentUser\Root', 'Cert:\CurrentUser\TrustedPublisher')
        }
    foreach ($store in $stores) {
        try {
            Import-Certificate -FilePath $cerPath -CertStoreLocation $store | Out-Null
            Write-Host "    trusted -> $store"
        } catch {
            Write-Warning "    FAILED  -> $store : $($_.Exception.Message)"
        }
    }
}

Write-Host ''
Write-Host '=== [4/4] Next step ===' -ForegroundColor Cyan
Write-Host "    powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 ``"
Write-Host "        -Path SuperHiVision_v1.5.24.exe,SuperHiVision_Setup_v1.5.24.exe"
Write-Host ''
Write-Host "    Thumbprint: $($cert.Thumbprint)" -ForegroundColor Green
Write-Host ''
