Add-Type -AssemblyName System.Device
$GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
$GeoWatcher.Start()

# Wait for a location reading
$startTime = Get-Date
while (($GeoWatcher.Status -ne 'Ready') -and ((Get-Date) - $startTime).TotalSeconds -lt 5) {
    Start-Sleep -Milliseconds 100
}

if ($GeoWatcher.Position.Location.IsUnknown) {
    Write-Host "{"
    Write-Host "    ""error"": ""Location unknown"","
    Write-Host "    ""latitude"": 0,"
    Write-Host "    ""longitude"": 0"
    Write-Host "}"
} else {
    $lat = $GeoWatcher.Position.Location.Latitude
    $lon = $GeoWatcher.Position.Location.Longitude
    Write-Host "{"
    Write-Host "    ""error"": null,"
    Write-Host "    ""latitude"": $lat,"
    Write-Host "    ""longitude"": $lon"
    Write-Host "}"
}

$GeoWatcher.Stop()