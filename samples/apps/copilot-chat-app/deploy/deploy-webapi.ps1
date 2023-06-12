
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

    [string]
    # Build configuration to publish.
    $BuildConfiguration = "Release",
    
    [string]
    # .NET framework to publish.
    $DotNetFramework = "net6.0",
    
    [string]
    # Target runtime to publish.
    $TargetRuntime = "win-x64",
    
    [string]
    # Output directory for published assets.
    $OutputDirectory = "$PSSCriptRoot"
)

az account show --output none
if ($LASTEXITCODE -ne 0) {
    Write-Host "Log into your Azure account"
    az login --output none
}

az account set -s $Subscription
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$publishOutputDirectory = "$OutputDirectory/publish"
$publishedZipDirectory = "$OutputDirectory/out"
$publishedZipFilePath = "$publishedZipDirectory/webapi.zip"
if (!(Test-Path $publishedZipDirectory)) {
    New-Item -ItemType Directory -Force -Path $publishedZipDirectory | Out-Null
}
if (!(Test-Path $publishOutputDirectory)) {
    New-Item -ItemType Directory -Force -Path $publishOutputDirectory | Out-Null
}

Write-Host "Build configuration: $BuildConfiguration"
dotnet publish ../webapi/CopilotChatWebApi.csproj --configuration $BuildConfiguration --framework $DotNetFramework --runtime $TargetRuntime --self-contained --output $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Compressing to $publishedZipFilePath"
Compress-Archive -Path $publishOutputDirectory\* -DestinationPath $publishedZipFilePath -Force

Write-Host "Getting Azure WebApp resource name..."
$webappName=$(az deployment group show --name $DeploymentName --resource-group $ResourceGroupName --output json | ConvertFrom-Json).properties.outputs.webapiName.value
if ($null -eq $webAppName) {
    Write-Error "Could not get Azure WebApp resource name from deployment output."
    exit 1
}

Write-Host "WebAPI name: $webappName"

Write-Host "Configuring Azure WebApp to run from package..."
az webapp config appsettings set --resource-group $ResourceGroupName --name $webappName --settings WEBSITE_RUN_FROM_PACKAGE="1" | out-null
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Deploying '$publishedZipFilePath' to Azure WebApp '$webappName'..."
az webapp deployment source config-zip --resource-group $ResourceGroupName --name $webappName --src $publishedZipFilePath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}