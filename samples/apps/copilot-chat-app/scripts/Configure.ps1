<#
.SYNOPSIS
Configure user secrets, appsettings.Development.json, and webapp/.env for Chat Copilot.
#>

Write-Host "#########################"
Write-Host "# Backend configuration #"
Write-Host "#########################"

# Install dev certificate
if ($IsLinux)
{
    dotnet dev-certs https
    if ($LASTEXITCODE -ne 0) { exit(1) }
}
else # Windows/MacOS
{
    dotnet dev-certs https --trust
    if ($LASTEXITCODE -ne 0) { exit(1) }
}

$webapiProjectPath = Join-Path "$PSScriptRoot" '../webapi'

Write-Host "Setting 'AIService:Key' user secret for $AIService..."
dotnet user-secrets set --project $webapiProjectPath  AIService:Key $ApiKey
if ($LASTEXITCODE -ne 0) { exit(1) }

$appsettingsOverrides = @{ AIService = @{ Type = $AIService; Endpoint = $Endpoint; Models = @{ Completion = $CompletionModel; Embedding = $EmbeddingModel; Planner = $PlannerModel } } }
$appSettingsJson = -join ("appsettings.", $envASPNetCore, ".json");
$appsettingsOverridesFilePath = Join-Path $webapiProjectPath $appSettingsJson

Write-Host "Setting up '$appSettingsJson' for $AIService..."
ConvertTo-Json $appsettingsOverrides | Out-File -Encoding utf8 $appsettingsOverridesFilePath

Write-Host "($appsettingsOverridesFilePath)"
Write-Host "========"
Get-Content $appsettingsOverridesFilePath | Write-Host
Write-Host "========"

Write-Host ""
Write-Host "##########################"
Write-Host "# Frontend configuration #"
Write-Host "##########################"

$webappProjectPath = Join-Path "$PSScriptRoot" '../webapi'
$webappEnvFilePath = Join-Path "$webappProjectPath" '/.env'

Write-Host "Setting up '.env'..."
Set-Content -Path $webappEnvFilePath -Value "REACT_APP_BACKEND_URI=https://localhost:40443/"
Add-Content -Path $webappEnvFilePath -Value "REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/$TenantId"
Add-Content -Path $webappEnvFilePath -Value "REACT_APP_AAD_CLIENT_ID=$ClientId"

Write-Host "($webappEnvFilePath)"
Write-Host "========"
Get-Content $webappEnvFilePath | Write-Host
Write-Host "========"

Write-Host "Done!"
