<#
.SYNOPSIS
Package CopilotChat's WebAPI for deployment to Azure
#>

param(
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
    $OutputDirectory = "$PSScriptRoot"
)

Write-Host "BuildConfiguration: $BuildConfiguration"
Write-Host "DotNetFramework: $DotNetFramework"
Write-Host "TargetRuntime: $TargetRuntime"
Write-Host "OutputDirectory: $OutputDirectory"

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
dotnet publish "$PSScriptRoot/../webapi/CopilotChatWebApi.csproj" --configuration $BuildConfiguration --framework $DotNetFramework --runtime $TargetRuntime --self-contained --output "$publishOutputDirectory"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Compressing to $publishedZipFilePath"
Compress-Archive -Path $publishOutputDirectory\* -DestinationPath $publishedZipFilePath -Force

Write-Host "Published webapi package to '$publishedZipFilePath'"