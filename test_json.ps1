$path = "c:\Users\jl_rb\Documents\antigravity\intelligent-chandrasekhar\street_dna\data\streets.geojson"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$json = $content | ConvertFrom-Json
Write-Host "JSON IS 100% VALID. TOTAL FEATURES: " $json.features.Count
