$ErrorActionPreference = "Stop"

$cssDir = "D:\Projects\VentaPOS\Desktop\sales\salesapp\static\css"
$jsDir = "D:\Projects\VentaPOS\Desktop\sales\salesapp\static\js"

Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path $cssDir | Out-Null
New-Item -ItemType Directory -Force -Path $jsDir | Out-Null

Write-Host "Downloading Tabler Core RTL CSS..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta20/dist/css/tabler.rtl.min.css" -OutFile "$cssDir\tabler.rtl.min.css"

Write-Host "Downloading Tabler Vendors RTL CSS..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta20/dist/css/tabler-vendors.rtl.min.css" -OutFile "$cssDir\tabler-vendors.rtl.min.css"

Write-Host "Downloading Tabler JS..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta20/dist/js/tabler.min.js" -OutFile "$jsDir\tabler.min.js"

Write-Host "`nAll files downloaded successfully for OFFLINE use! 🎉"
Write-Host "Now you can change base.html to use the local files."
Pause
