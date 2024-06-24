# This script is for local use to analyze code coverage in more detail using HTML report.

Param(
    [switch]$ProdPackagesOnly = $false
)

# Generate a timestamp for the current date and time
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# Define paths
$scriptPath = Get-Item -Path $PSScriptRoot
$coverageOutputPath = Join-Path $scriptPath "TestResults\Coverage\$timestamp"
$reportOutputPath = Join-Path $scriptPath "TestResults\Reports\$timestamp"

# Create output directories
New-Item -ItemType Directory -Force -Path $coverageOutputPath
New-Item -ItemType Directory -Force -Path $reportOutputPath

# Find tests for projects ending with 'UnitTests.csproj'
$testProjects = Get-ChildItem $scriptPath -Filter "*UnitTests.csproj" -Recurse

foreach ($project in $testProjects) {
    $testProjectPath = $project.FullName
    Write-Host "Running tests for project: $($testProjectPath)"

    # Run tests
    dotnet test $testProjectPath `
        --collect:"XPlat Code Coverage" `
        --results-directory:$coverageOutputPath `
        -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.ExcludeByAttribute=GeneratedCodeAttribute,CompilerGeneratedAttribute,ExcludeFromCodeCoverageAttribute `

}

# Install required tools
& dotnet tool install -g coverlet.console
& dotnet tool install -g dotnet-reportgenerator-globaltool

# Generate HTML report
if ($ProdPackagesOnly) {
    $assemblies = @(
        "+Microsoft.SemanticKernel.Abstractions",
        "+Microsoft.SemanticKernel.Core",
        "+Microsoft.SemanticKernel.PromptTemplates.Handlebars",
        "+Microsoft.SemanticKernel.Connectors.OpenAI",
        "+Microsoft.SemanticKernel.Yaml"
    )

    $assemblyFilters = $assemblies -join ";"

    # Generate report for production assemblies only
    & reportgenerator -reports:"$coverageOutputPath/**/coverage.cobertura.xml" -targetdir:$reportOutputPath -reporttypes:Html -assemblyfilters:$assemblyFilters
}
else {
    & reportgenerator -reports:"$coverageOutputPath/**/coverage.cobertura.xml" -targetdir:$reportOutputPath -reporttypes:Html
}

Write-Host "Code coverage report generated at: $reportOutputPath"

# Open report
$reportIndexHtml = Join-Path $reportOutputPath "index.html"
Invoke-Item -Path $reportIndexHtml
