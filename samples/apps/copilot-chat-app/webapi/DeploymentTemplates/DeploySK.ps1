<#
.SYNOPSIS
Creates a Semantic Kernel service deployment.
#>

param(
    [Parameter(Mandatory)]
    [string]
    # Name for the deployment
    $DeploymentName,

    [Parameter(Mandatory)]
    [string]
    # Subscription to which to make the deployment
    $Subscription,

    [string]
    # Resource group to which to make the deployment
    $ResourceGroup = "",

    [string]
    # Region to which to make the deployment (ignored when deploying to an existing resource group)
    $Region = "South Central US",

    [string]
    # Package to deploy to web service
    $PackageUri = 'https://skaasdeploy.blob.core.windows.net/api/skaas.zip',

    [string]
    # SKU for the Azure App Service plan
    $AppServiceSku = "B1",

    [switch]
    # Don't deploy Qdrant for memory storage - Use volatile memory instead
    $NoQdrant,

    [switch]
    # Don't deploy Cosmos DB for chat storage - Use volatile memory instead
    $NoCosmosDb,

    [switch]
    # Don't deploy Speech Services to enable speech as chat input
    $NoSpeechServices,

    [switch]
    # Switches on verbose template deployment output
    $DebugDeployment
)

$jsonConfig = "
{
    `\`"name`\`": { `\`"value`\`": `\`"$DeploymentName`\`" },
    `\`"packageUri`\`": { `\`"value`\`": `\`"$PackageUri`\`" },
    `\`"appServiceSku`\`": { `\`"value`\`": `\`"$AppServiceSku`\`" },
    `\`"deployQdrant`\`": { `\`"value`\`": $(If (!($NoQdrant)) {"true"} Else {"false"}) },
    `\`"deployCosmosDB`\`": { `\`"value`\`": $(If (!($NoSpeechServices)) {"true"} Else {"false"}) },
    `\`"deploySpeechServices`\`": { `\`"value`\`": $(If (!($NoSpeechServices)) {"true"} Else {"false"}) }
}
"

$jsonConfig = $jsonConfig -replace '\s',''

$ErrorActionPreference = "Stop"

$templateFile = "$($PSScriptRoot)/sk.bicep"

if (!$ResourceGroup)
{
    $ResourceGroup = "rg-" + $DeploymentName
}

Write-Host "Log into your Azure account"
az login | out-null

az account set -s $Subscription
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Creating resource group $($ResourceGroup) if it doesn't exist..."
az group create --location $Region --name $ResourceGroup --tags Creator=$env:UserName
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Validating template file..."
az deployment group validate --name $DeploymentName --resource-group $ResourceGroup --template-file $templateFile --parameters $jsonConfig
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Deploying..."
if ($DebugDeployment) {
    az deployment group create --name $DeploymentName --resource-group $ResourceGroup --template-file $templateFile --debug --parameters $jsonConfig
}
else {
    az deployment group create --name $DeploymentName --resource-group $ResourceGroup --template-file $templateFile --parameters $jsonConfig
}