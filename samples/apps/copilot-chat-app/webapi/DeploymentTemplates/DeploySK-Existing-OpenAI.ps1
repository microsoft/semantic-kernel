<#
.SYNOPSIS
Creates a Semantic Kernel service deployment using an existing OpenAI account.
#>

param(
    [Parameter(Mandatory)]
    [string]
    # Name for the deployment
    $DeploymentName,

    [Parameter(Mandatory)]
    [string]
    # OpenAI API key
    $ApiKey,

    [string]
    # Model to use for chat completions
    $CompletionModel = "gpt-3.5-turbo",

    [string]
    # Model to use for text embeddings
    $EmbeddingModel = "text-embedding-ada-002",

    [string]
    # Completion model the task planner should use
    $PlannerModel = "gpt-3.5-turbo",

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
    $PackageUri = 'https://skaasdeploy.blob.core.windows.net/api/semantickernelapi.zip',

    [string]
    # SKU for the Azure App Service plan
    $AppServiceSku = "B1",

    [string]
    # API key to access Semantic Kernel server's endpoints
    $SemanticKernelApiKey = "$([guid]::NewGuid())",

    # TODO: Temporarily disabling qdrant deployment while we secure its endpoint.
    # [switch]
    # # Don't deploy Qdrant for memory storage - Use volatile memory instead
    # $NoQdrant,

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

$NoQdrant = $true # TODO: Temporarily disabling qdrant deployment while we secure its endpoint.

$jsonConfig = "
{
    `\`"name`\`": { `\`"value`\`": `\`"$DeploymentName`\`" },
    `\`"apiKey`\`": { `\`"value`\`": `\`"$ApiKey`\`" },
    `\`"completionModel`\`": { `\`"value`\`": `\`"$CompletionModel`\`" },
    `\`"embeddingModel`\`": { `\`"value`\`": `\`"$EmbeddingModel`\`" },
    `\`"plannerModel`\`": { `\`"value`\`": `\`"$PlannerModel`\`" },
    `\`"packageUri`\`": { `\`"value`\`": `\`"$PackageUri`\`" },
    `\`"appServiceSku`\`": { `\`"value`\`": `\`"$AppServiceSku`\`" },
    `\`"semanticKernelApiKey`\`": { `\`"value`\`": `\`"$SemanticKernelApiKey`\`" },
    `\`"deployQdrant`\`": { `\`"value`\`": $(If (!($NoQdrant)) {"true"} Else {"false"}) },
    `\`"deployCosmosDB`\`": { `\`"value`\`": $(If (!($NoSpeechServices)) {"true"} Else {"false"}) },
    `\`"deploySpeechServices`\`": { `\`"value`\`": $(If (!($NoSpeechServices)) {"true"} Else {"false"}) }
}
"

$jsonConfig = $jsonConfig -replace '\s',''

$ErrorActionPreference = "Stop"

$templateFile = "$($PSScriptRoot)/sk-existing-openai.bicep"

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