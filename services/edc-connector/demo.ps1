# Demonstration Module 2 : 2 usines, 4 scenarios, sauvegarde des journaux, nettoyage.
# Usage (depuis la racine du depot) : powershell -ExecutionPolicy Bypass -File services\edc-connector\demo.ps1
$ErrorActionPreference = "Continue"
$out = "services\edc-connector\demo_logs"
New-Item -ItemType Directory -Force $out | Out-Null

docker rm -f edc-connector-usine-1 edc-connector-usine-2 2>$null | Out-Null
docker network rm dsnet 2>$null | Out-Null
docker network create dsnet | Out-Null
docker build -q -f services/edc-connector/Dockerfile -t dataspace/edc-connector . | Out-Null

foreach ($i in 1,2) {
  docker run -d --name "edc-connector-usine-$i" --network dsnet -p "1810${i}:8000" `
    -e "USINE_ID=usine_$i" -v "${PWD}/Simulation_Usine/data:/data:ro" dataspace/edc-connector | Out-Null
}
foreach ($p in 18101,18102) {
  for ($t = 0; $t -lt 30; $t++) {
    try { Invoke-RestMethod "http://localhost:$p/healthz" | Out-Null; break } catch { Start-Sleep 1 }
  }
}

function Neg($asset) {
  Invoke-RestMethod -Method Post -Uri http://localhost:18101/negotiate -ContentType application/json `
    -Body (@{provider="usine_2"; asset=$asset} | ConvertTo-Json)
}
$results = @()

# S1 : acces autorise
$n = Neg "iot-usine-2-historical"
$detail = $n.state
if ($n.state -eq "FINALIZED") {
  $tr = Invoke-RestMethod -Method Post -Uri http://localhost:18101/transfer -ContentType application/json `
        -Body (@{negotiation_id=$n.negotiation_id} | ConvertTo-Json)
  $detail = "$($n.state), transfert HTTP $($tr.http_status), $($tr.rows) lignes"
}
$results += [pscustomobject]@{Scenario="S1 politique valide"; Attendu="FINALIZED + transfert"; Obtenu=$detail}

# S2 : politique expiree
$n = Neg "iot-usine-2-expired"
$results += [pscustomobject]@{Scenario="S2 politique expiree"; Attendu="TERMINATED"; Obtenu="$($n.state) : $($n.reason)"}

# S3 : asset non publie
$n = Neg "iot-usine-2-hidden"
$results += [pscustomobject]@{Scenario="S3 asset non publie"; Attendu="TERMINATED"; Obtenu="$($n.state) : $($n.reason)"}

# S4 : acces sans accord valide
try { Invoke-RestMethod http://localhost:18102/dsp/data/ag-inexistant | Out-Null; $code = 200 }
catch { $code = $_.Exception.Response.StatusCode.value__ }
$results += [pscustomobject]@{Scenario="S4 acces sans accord"; Attendu="403"; Obtenu="$code"}

$results | Format-Table -AutoSize -Wrap
$results | ConvertTo-Json | Out-File "$out\resultats_tests.json" -Encoding utf8

# Sauvegarde des journaux AVANT le nettoyage
foreach ($i in 1,2) {
  Invoke-RestMethod "http://localhost:1810${i}/logs" | ConvertTo-Json -Depth 8 | Out-File "$out\logs_usine_$i.json" -Encoding utf8
  Invoke-RestMethod "http://localhost:1810${i}/contracts" | ConvertTo-Json -Depth 8 | Out-File "$out\contracts_usine_$i.json" -Encoding utf8
}
Write-Host "Journaux sauvegardes dans $out"

docker rm -f edc-connector-usine-1 edc-connector-usine-2 | Out-Null
docker network rm dsnet | Out-Null