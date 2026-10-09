# =============================================================================
#  sign_binaries.ps1 - Super Hi Vision
#
#  Signs the built binaries (green exe / installer) with the SevenZeroMeowTeam
#  code-signing certificate, so Windows shows a publisher instead of
#  "Unknown publisher".
#
#  Two interchangeable back-ends, picked automatically:
#    1. signtool.exe - Microsoft's own tool from the Windows SDK (also the only
#       way to drive an EV hardware token). Looked up on PATH and under
#       "Windows Kits\10\bin\<version>\x64".
#    2. PowerShell Set-AuthenticodeSignature - built into Windows, needs no SDK.
#       Used when signtool is absent, or forced with -SignMethod PowerShell.
#  Both produce the same Authenticode signature, and the result is verified with
#  Get-AuthenticodeSignature either way.
#
#  A signature is appended to the file; the program itself is not modified, but
#  the hash changes. Each file is copied to <name>.unsigned first (unless
#  -NoBackup), so you can always roll back.
#
#  ASCII only on purpose (Windows PowerShell 5.1 + files without BOM).
#
#  Usage:
#     powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 `
#         -Path SuperHiVision_v1.5.25.exe,SuperHiVision_Setup_v1.5.25.exe
#
#     # by explicit thumbprint (e.g. in CI, after importing a .pfx):
#     powershell -ExecutionPolicy Bypass -File tools\sign_binaries.ps1 `
#         -Path dist\SuperHiVision_v1.5.25.exe -Thumbprint ABC123...
#
#     # force a back-end (testing, EV token, no-SDK boxes):
#     ... -SignMethod Signtool
#     ... -SignMethod PowerShell
#     ... -SigntoolPath "C:\path\to\signtool.exe"
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

    # Auto: signtool if available, else PowerShell.
    [ValidateSet('Auto', 'Signtool', 'PowerShell')]
    [string] $SignMethod = 'Auto',

    # Explicit signtool.exe path; skips the search.
    [string] $SigntoolPath,

    # Skip the "<name>.unsigned" backup copy.
    [switch] $NoBackup,

    # Do not fail the whole run when one file cannot be signed.
    [switch] $ContinueOnError
)

$ErrorActionPreference = 'Stop'


function Get-SigningCertificate {
    param([string] $WantThumbprint, [string] $WantSubject)

    foreach ($store in @('Cert:\CurrentUser\My', 'Cert:\LocalMachine\My')) {
        $candidates = @(Get-ChildItem $store -ErrorAction SilentlyContinue)
        if ($WantThumbprint) {
            $hit = $candidates | Where-Object { $_.Thumbprint -eq $WantThumbprint }
        } else {
            $hit = $candidates | Where-Object { $_.Subject -eq $WantSubject }
        }
        $hit = @($hit) | Where-Object { $_.HasPrivateKey }
        if ($hit.Count -gt 0) {
            return [pscustomobject]@{
                Cert    = @($hit)[0]
                Store   = $store
                Machine = ($store -like '*LocalMachine*')
            }
        }
    }
    return $null
}


function Find-Signtool {
    param([string] $Explicit)

    if ($Explicit) {
        if (Test-Path -LiteralPath $Explicit) { return (Resolve-Path -LiteralPath $Explicit).Path }
        Write-Warning "    -SigntoolPath not found: $Explicit"
    }

    # 1. already on PATH
    $onPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }

    # 2. Windows SDK: newest kit first, then the legacy bin\x64 layout
    $candidates = @()
    $binRoots = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'),
        (Join-Path $env:ProgramFiles 'Windows Kits\10\bin')
    )
    foreach ($root in $binRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $versioned = @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^\d+(\.\d+)+$' } |
            Sort-Object { [version]$_.Name } -Descending)
        foreach ($dir in $versioned) {
            $candidates += (Join-Path $dir.FullName 'x64\signtool.exe')
        }
        $candidates += (Join-Path $root 'x64\signtool.exe')
    }

    # 3. the App Certification Kit ships a copy as well
    $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\App Certification Kit\signtool.exe')

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    return $null
}


Write-Host ''
Write-Host '=== Resolve signing certificate ===' -ForegroundColor Cyan
$found = Get-SigningCertificate -WantThumbprint $Thumbprint -WantSubject $Subject
if (-not $found) {
    $want = if ($Thumbprint) { "thumbprint $Thumbprint" } else { "subject $Subject" }
    Write-Host "    NOT FOUND: no certificate with a private key for $want" -ForegroundColor Red
    Write-Host '    Create one first:  tools\create_signing_cert.ps1' -ForegroundColor Yellow
    exit 2
}
$cert = $found.Cert
Write-Host "    Subject    : $($cert.Subject)"
Write-Host "    Thumbprint : $($cert.Thumbprint)"
Write-Host "    Expires    : $($cert.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "    Store      : $($found.Store)"

Write-Host ''
Write-Host '=== Resolve signing tool ===' -ForegroundColor Cyan
$signtool = $null
if ($SignMethod -ne 'PowerShell') {
    $signtool = Find-Signtool -Explicit $SigntoolPath
}
if ($SignMethod -eq 'Signtool' -and -not $signtool) {
    Write-Host '    -SignMethod Signtool was requested but signtool.exe was not found.' -ForegroundColor Red
    Write-Host '    Install the Windows SDK, pass -SigntoolPath, or use -SignMethod PowerShell.' -ForegroundColor Yellow
    exit 4
}
if ($signtool) {
    Write-Host '    back-end : signtool.exe (Microsoft Authenticode tool)'
    Write-Host "    path     : $signtool"
    Write-Host "    command  : signtool sign /sha1 $($cert.Thumbprint) /fd SHA256 /tr $TimestampServer /td SHA256 <file>"
} else {
    Write-Host '    back-end : PowerShell Set-AuthenticodeSignature (no SDK needed)'
    if ($SignMethod -eq 'Auto') {
        Write-Host '    (signtool.exe not found on this machine - that is fine)'
    }
}

$results = @()
foreach ($file in $Path) {
    Write-Host ''
    Write-Host "=== Sign: $file ===" -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $file)) {
        Write-Host '    MISSING - skipped' -ForegroundColor Red
        $results += [pscustomobject]@{ File = $file; Status = 'Missing'; Backend = '-'; Timestamp = '-' }
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
            Write-Host '    backup  -> already exists, kept'
        }
    }

    # ---- sign it ---------------------------------------------------------
    if ($signtool) {
        $usedBackend = 'signtool'

        # Build the argument list inline (no helper function - a function call
        # here produced a command line PowerShell could not run). Splatting a
        # plain array is the form that behaved identically in every shell tested.
        $attempt = @('sign', '/sha1', $cert.Thumbprint, '/fd', 'SHA256')
        if ($found.Machine) { $attempt += '/sm' }
        if ($TimestampServer) { $attempt += @('/tr', $TimestampServer, '/td', 'SHA256') }
        $attempt += $full
        Write-Host "    call    : $signtool $($attempt -join ' ')"
        & $signtool @attempt

        if ((Get-AuthenticodeSignature -LiteralPath $full).Status -ne 'Valid') {
            Write-Host '    no valid signature yet - retrying without a timestamp...' -ForegroundColor Yellow
            $retry = @('sign', '/sha1', $cert.Thumbprint, '/fd', 'SHA256')
            if ($found.Machine) { $retry += '/sm' }
            $retry += $full
            Write-Host "    call    : $signtool $($retry -join ' ')"
            & $signtool @retry
        }
    } else {
        # Try with a timestamp first; fall back to a plain signature offline.
        $usedBackend = 'PowerShell'
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
    }

    # ---- verify, whatever the back-end did -------------------------------
    $sig = Get-AuthenticodeSignature -LiteralPath $full
    $after = $sig.Status
    $signer = if ($sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { '(none)' }
    $ts = if ($sig.TimeStamperCertificate) { 'yes' } else { 'no' }

    Write-Host "    before  : $before"
    Write-Host "    after   : $after"
    Write-Host "    signer  : $signer"
    Write-Host "    timestamp: $ts"

    if ($after -eq 'Valid') {
        Write-Host "    OK  ($usedBackend)" -ForegroundColor Green
    } else {
        Write-Host "    FAILED ($usedBackend): $($sig.StatusMessage)" -ForegroundColor Red
    }

    $results += [pscustomobject]@{
        File      = (Split-Path -Leaf $full)
        Status    = $after
        Backend   = $usedBackend
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
