# =============================================================================
#  sign_binaries.ps1 - Super Hi Vision
#
#  Signs the built binaries (green exe / installer) with the SevenZeroMeowTeam
#  code-signing certificate, so Windows shows a publisher instead of
#  "Unknown publisher".
#
#  A signature is appended to the file; the program itself is not modified,
#  but the file hash changes. Each file is copied to <name>.unsigned before
#  signing unless -NoBackup is passed, so you can always roll back.
#
#  ASCII only on purpose (Windows PowerShell 5.1 + files without BOM).
#
#  Usage:
#     powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 `
#         -Path SuperHiVision_v1.5.24.exe,SuperHiVision_Setup_v1.5.24.exe
#
#     # by explicit thumbprint (e.g. in CI, after importing a .pfx):
#     powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 `
#         -Path dist\SuperHiVision_v1.5.24.exe -Thumbprint ABC123...
# =============================================================================
[CmdletBinding()]
param(
    # One or more files to sign.
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]] $Path,

    # Certificate subject to look up (used when -Thumbprint is not given).
    [string] $Subject = 'CN=SevenZeroMeowTeam',

    # Exact certificate thumbprint; wins over -Subject.
    [string] $Thumbprint,

    # RFC3161 timestamp server. Without a timestamp the signature stops being
    # valid once the certificate expires, so this is on by default.
    [string] $TimestampServer = 'http://timestamp.digicert.com',

    # Skip the "<name>.unsigned" backup copy.
    [switch] $NoBackup,

    # Do not fail the whole run when one file cannot be signed.
    [switch] $ContinueOnError
)

$ErrorActionPreference = 'Stop'

function Get-SigningCertificate {
    param([string] $Thumbprint, [string] $Subject)

    foreach ($store in @('Cert:\CurrentUser\My', 'Cert:\LocalMachine\My')) {
        $candidates = @(Get-ChildItem $store -ErrorAction SilentlyContinue)
        if ($Thumbprint) {
            $hit = $candidates | Where-Object { $_.Thumbprint -eq $Thumbprint }
        } else {
            $hit = $candidates | Where-Object { $_.Subject -eq $Subject }
        }
        $hit = @($hit) | Where-Object { $_.HasPrivateKey }
        if ($hit.Count -gt 0) { return @($hit)[0] }
    }
    return $null
}

Write-Host ''
Write-Host '=== Resolve signing certificate ===' -ForegroundColor Cyan
$cert = Get-SigningCertificate -Thumbprint $Thumbprint -Subject $Subject
if (-not $cert) {
    $want = if ($Thumbprint) { "thumbprint $Thumbprint" } else { "subject $Subject" }
    Write-Host "    NOT FOUND: no certificate with a private key for $want" -ForegroundColor Red
    Write-Host '    Create one first:  tools\create_signing_cert.ps1' -ForegroundColor Yellow
    exit 2
}
Write-Host "    Subject    : $($cert.Subject)"
Write-Host "    Thumbprint : $($cert.Thumbprint)"
Write-Host "    Expires    : $($cert.NotAfter.ToString('yyyy-MM-dd'))"

$results = @()
foreach ($file in $Path) {
    Write-Host ''
    Write-Host "=== Sign: $file ===" -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $file)) {
        Write-Host '    MISSING - skipped' -ForegroundColor Red
        $results += [pscustomobject]@{ File = $file; Status = 'Missing' }
        if (-not $ContinueOnError) { exit 3 }
        continue
    }

    $full = (Resolve-Path -LiteralPath $file).Path
    $before = (Get-AuthenticodeSignature -LiteralPath $full).Status

    if (-not $NoBackup) {
        $backup = "$full.unsigned"
        if (-not (Test-Path -LiteralPath $backup)) {
            Copy-Item -LiteralPath $full -Destination $backup -Force
            Write-Host "    backup  -> $backup"
        } else {
            Write-Host "    backup  -> already exists, kept"
        }
    }

    # Try with a timestamp first; fall back to a plain signature offline.
    $sig = $null
    try {
        $sig = Set-AuthenticodeSignature -LiteralPath $full -Certificate $cert `
            -HashAlgorithm SHA256 -TimestampServer $TimestampServer
    } catch {
        Write-Warning "    timestamp step failed: $($_.Exception.Message)"
    }

    if (-not $sig -or $sig.Status -ne 'Valid') {
        Write-Host '    retrying without timestamp...' -ForegroundColor Yellow
        $sig = Set-AuthenticodeSignature -LiteralPath $full -Certificate $cert -HashAlgorithm SHA256
    }

    $after = $sig.Status
    $signer = if ($sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { '(none)' }
    $ts = if ($sig.TimeStamperCertificate) { 'yes' } else { 'no' }

    Write-Host "    before  : $before"
    Write-Host "    after   : $after"
    Write-Host "    signer  : $signer"
    Write-Host "    timestamp: $ts"

    if ($after -eq 'Valid') {
        Write-Host '    OK' -ForegroundColor Green
    } else {
        Write-Host "    FAILED: $($sig.StatusMessage)" -ForegroundColor Red
    }

    $results += [pscustomobject]@{
        File      = (Split-Path -Leaf $full)
        Status    = $after
        Signer    = $signer
        Timestamp = $ts
    }
}

Write-Host ''
Write-Host '=== Summary ===' -ForegroundColor Cyan
$results | Format-Table -AutoSize

$failed = @($results | Where-Object { $_.Status -ne 'Valid' })
if ($failed.Count -gt 0) { exit 1 }
Write-Host 'All files signed.' -ForegroundColor Green
exit 0
