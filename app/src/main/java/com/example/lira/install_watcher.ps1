$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$apk = "$PSScriptRoot\Lira-app-debug.apk"

Write-Host "Monitoring for device connection..." -ForegroundColor Cyan

while ($true) {
    $lines = & $adb devices
    $devLines = $lines | Where-Object { $_ -match '^[a-zA-Z0-9_\.:-]+\s+(device|unauthorized)' }
    if ($devLines) {
        $first = $devLines[0].Trim()
        $parts = $first -split '\s+'
        $devId = $parts[0]
        $state = $parts[1]

        if ($state -eq "unauthorized") {
            Write-Host "[WAIT] Device $devId is unauthorized. Please tap 'Allow USB debugging' on your phone!" -ForegroundColor Magenta
        } elseif ($state -eq "device") {
            Write-Host "[FOUND] Active Device: $devId" -ForegroundColor Green
            Write-Host "Installing APK (Watch phone screen for 'Install' or Play Protect prompt)..." -ForegroundColor Yellow

            $res = & $adb -s $devId install -r -t -g $apk
            Write-Host $res

            if ($res -match "Success") {
                Write-Host "[SUCCESS] LIRA installed on device $devId!" -ForegroundColor Green
                & $adb -s $devId shell am start -n com.example.lira/.MainActivity
                break
            } else {
                # Fallback push and pm install
                Write-Host "Trying fallback pm install..." -ForegroundColor Yellow
                & $adb -s $devId push $apk /data/local/tmp/lira.apk
                $pmRes = & $adb -s $devId shell pm install -r -t -g /data/local/tmp/lira.apk
                Write-Host "pm result: $pmRes"
                if ($pmRes -match "Success") {
                    Write-Host "[SUCCESS] LIRA installed successfully via pm!" -ForegroundColor Green
                    & $adb -s $devId shell am start -n com.example.lira/.MainActivity
                    break
                }
            }
        }
    }
    Start-Sleep -Seconds 3
}
