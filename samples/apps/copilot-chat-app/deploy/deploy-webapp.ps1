
param(
    [Parameter(Mandatory)]
    [string]
    # Subscription to which to make the deployment
    $Subscription,

    [Parameter(Mandatory)]
    [string]
    # Resource group to which to make the deployment
    $ResourceGroupName,
    
    [Parameter(Mandatory)]
    [string]
    # Name of the previously deployed Azure deployment 
    $DeploymentName,

    [Parameter(Mandatory)]
    [string]
    # Name of the previously deployed Azure deployment 
    $ApplicationClientId
)

Write-Host "Setting up Azure credentials..."
az account show --output none
if ($LASTEXITCODE -ne 0) {
    Write-Host "Log into your Azure account"
    az login --output none
}

Write-Host "Setting subscription to '$Subscription'..."
az account set -s $Subscription
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Getting deployment outputs..."
$deployment=$(az deployment group show --name $DeploymentName --resource-group $ResourceGroupName --output json | ConvertFrom-Json)
$webappUrl=$deployment.properties.outputs.webappUrl.value
$webapiUrl=$deployment.properties.outputs.webapiUrl.value
$webapiName=$deployment.properties.outputs.webapiName.value
$webapiApiKey=($(az webapp config appsettings list --name $webapiName --resource-group $ResourceGroupName | ConvertFrom-JSON) | Where-Object -Property name -EQ -Value Authorization:ApiKey).value
Write-Host "webappUrl: $webappUrl"
Write-Host "webapiName: $webapiName"
Write-Host "webapiUrl: $webapiUrl"

# Set UTF8 as default encoding for Out-File
$PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

$envFilePath="$PSSCriptRoot/../webapp/.env"
Write-Host "Writing environment variables to '$envFilePath'..."
"REACT_APP_BACKEND_URI=https://$webapiUrl/" | Out-File -FilePath $envFilePath
"REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common" | Out-File -FilePath $envFilePath -Append
"REACT_APP_AAD_CLIENT_ID=$ApplicationClientId" | Out-File -FilePath $envFilePath -Append
"REACT_APP_SK_API_KEY=$webapiApiKey" | Out-File -FilePath $envFilePath -Append

$swaConfigFilePath="$PSSCriptRoot/../webapp/swa-cli.config.json"
"{" | Out-File -FilePath $swaConfigFilePath
"  `"`$schema`": `"https://aka.ms/azure/static-web-apps-cli/schema`"," | Out-File -FilePath $swaConfigFilePath -Append
"    `"configurations`": {" | Out-File -FilePath $swaConfigFilePath -Append
"      `"webapp`": {" | Out-File -FilePath $swaConfigFilePath -Append
"      `"appLocation`": `".`"," | Out-File -FilePath $swaConfigFilePath -Append
"      `"outputLocation`": `"./out`"," | Out-File -FilePath $swaConfigFilePath -Append
"      `"appBuildCommand`": `"yarn build`"," | Out-File -FilePath $swaConfigFilePath -Append
"      `"run`": `"yarn start`"," | Out-File -FilePath $swaConfigFilePath -Append
"      `"appDevserverUrl`": `"https://$webappUrl`"" | Out-File -FilePath $swaConfigFilePath -Append
"    }" | Out-File -FilePath $swaConfigFilePath -Append
"  }" | Out-File -FilePath $swaConfigFilePath -Append
"}" | Out-File -FilePath $swaConfigFilePath -Append


Push-Location -Path "$PSSCriptRoot/../webapp"
Write-Host "Installing yarn dependencies..."
yarn install
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Building webapp..."
swa build
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Deploying webapp..."
swa deploy --subscription-id 5b742c40-bc2b-4a4f-902f-ee9f644d8844 --app-name swa-cc-int-cus-001-iudsttm4r2eg4 --env production
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Pop-Location
