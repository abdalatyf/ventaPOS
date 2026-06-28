@echo off
color 0A
echo ========================================================
echo        VentaPOS - Offline Assets Downloader
echo ========================================================
echo.
echo Please wait, downloading Tabler files...
echo.

powershell -ExecutionPolicy Bypass -NoProfile -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $cssDir = 'D:\Projects\VentaPOS\Desktop\sales\salesapp\static\css'; $jsDir = 'D:\Projects\VentaPOS\Desktop\sales\salesapp\static\js'; New-Item -ItemType Directory -Force -Path $cssDir | Out-Null; New-Item -ItemType Directory -Force -Path $jsDir | Out-Null; Write-Host '1/3 Downloading RTL CSS (unpkg)...'; Invoke-WebRequest -Uri 'https://unpkg.com/@tabler/core@1.0.0-beta20/dist/css/tabler.rtl.min.css' -OutFile \"$cssDir\tabler.rtl.min.css\"; Write-Host '2/3 Downloading RTL Vendors CSS...'; Invoke-WebRequest -Uri 'https://unpkg.com/@tabler/core@1.0.0-beta20/dist/css/tabler-vendors.rtl.min.css' -OutFile \"$cssDir\tabler-vendors.rtl.min.css\"; Write-Host '3/3 Downloading JS...'; Invoke-WebRequest -Uri 'https://unpkg.com/@tabler/core@1.0.0-beta20/dist/js/tabler.min.js' -OutFile \"$jsDir\tabler.min.js\"; Write-Host '`nSUCCESS! All files are downloaded for Offline use. You can close this window now.'"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo --------------------------------------------------------
    echo ERROR: Something went wrong. Please check your internet.
    echo --------------------------------------------------------
) else (
    echo.
    echo ========================================================
    echo DONE! The files have been placed in the static folder.
    echo ========================================================
)

echo.
pause
