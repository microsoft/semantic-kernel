param([string]$targetNetFramework)

$targetNetFramework = "net$targetNetFramework"

$rootDirectory = Get-Location

Write-Host "Publishing the SemanticKernel.AotTests application."

dotnet publish $rootDirectory/dotnet/src/SemanticKernel.AotTests/SemanticKernel.AotTests.csproj --framework $targetNetFramework | Tee-Object -Variable publishOutput

$warningFound = $false

if ($LastExitCode -ne 0)
{
    Write-Host "Errors were detected while publishing the application. See the output for more details."
    Exit $LastExitCode
}
elseif ($publishOutput -like "*analysis warning IL*" -or $publishOutput -like "*analysis error IL*")
{
    Write-Host "Native AOT analysis warnings were detected while publishing the application. See the output for more details."
    Exit 1
}

Write-Host "The application was published successfully."

$runtime = $IsWindows ? "win-x64" : "linux-x64"

$appPublishDirectory = Join-Path -Path $rootDirectory -ChildPath dotnet/src/SemanticKernel.AotTests/bin/Release/$targetNetFramework/$runtime/publish

$appFileName = $IsWindows ? "SemanticKernel.AotTests.exe" : "SemanticKernel.AotTests"

$app = Join-Path -Path $appPublishDirectory -ChildPath $appFileName

Write-Host "Executing the SemanticKernel.AotTests application."

& $app

if ($LastExitCode -ne 0)
{
    $testPassed = 1
    Write-Host "There was an error while executing the application. The Last Exit Code is: $LastExitCode"
}
else
{
    Write-Host "The application was executed successfully."
}

Exit $testPassed