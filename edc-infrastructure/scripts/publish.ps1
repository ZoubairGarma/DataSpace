param([string]$N, [int]$Port)
$M = "http://localhost:$Port/management/v3"
$H = "Content-Type: application/json"

function Send($path, $file, $assetId) {
  $b = Get-Content $file -Raw
  $b = $b -replace "__N__", $N -replace "__POLICY__", "policy-ok"
  if ($assetId) { $b = $b -replace "__ASSET__", $assetId }
  if ($b -match "__[A-Z]+__") { throw "Placeholder non substitue : $($Matches[0])" }
  $b | curl.exe -s -X POST "$M/$path" -H $H --data-binary "@-"
  Write-Host ""
}

Send "policydefinitions" "scripts/payloads/policy_ok.json"
foreach ($t in "live","historical") {
  Send "assets" "scripts/payloads/asset_$t.json"
  Send "contractdefinitions" "scripts/payloads/contractdef.json" "iot-usine-$N-$t"
}