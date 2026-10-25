# ==============================================================================
# LIRA — Automatic Mobile APK Installer Script
# ==============================================================================

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$apk = "$PSScriptRoot\Lira-app-debug.apk"

if (!(Test-Path $adb)) {
    Write-Host "[ERROR] adb.exe not found at $adb" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   LIRA Mobile APK Installer" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Waiting for Android mobile device to connect via USB..." -ForegroundColor Yellow
Write-Host "(Ensure USB Debugging is ON and tap 'Allow' on your phone)" -ForegroundColor DarkGray

while ($true) {
    $devices = & $adb devices | Select-String -Pattern "\b(device|unauthorized)\b"
    if ($devices) {
        $devLine = $devices[0].ToString()
        if ($devLine -match "unauthorized") {
            Write-Host "[PROMPT] Mobile device detected but unauthorized. Please tap 'Allow USB debugging' on your phone screen!" -ForegroundColor Magenta
            Start-Sleep -Seconds 3
            continue
        } elseif ($devLine -match "device") {
            Write-Host "[SUCCESS] Connected Device: $devLine" -ForegroundColor Green
            break
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "`nInstalling Lira-app-debug.apk on your mobile..." -ForegroundColor Cyan
$installOutput = & $adb install -r $apk
Write-Host $installOutput

if ($installOutput -match "Success") {
    Write-Host "`n[SUCCESS] LIRA installed successfully on your phone!" -ForegroundColor Green
    Write-Host "Launching LIRA..." -ForegroundColor Cyan
    & $adb shell am start -n com.example.lira/.MainActivity
} else {
    Write-Host "`n[NOTICE] If install failed, ensure USB debugging is authorized." -ForegroundColor Yellow
}
