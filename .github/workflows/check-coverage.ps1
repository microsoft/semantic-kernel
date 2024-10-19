param (
    [string]$JsonReportPath,
    [double]$CoverageThreshold
)

$jsonContent = Get-Content $JsonReportPath -Raw | ConvertFrom-Json
$coverageBelowThreshold = $false

$nonExperimentalAssemblies = [System.Collections.Generic.HashSet[string]]::new()
$nonExperimentalAssemblies.AddRange(@(
    'Microsoft.SemanticKernel.Abstractions'
    'Microsoft.SemanticKernel.Core'
    'Microsoft.SemanticKernel.PromptTemplates.Handlebars'
    'Microsoft.SemanticKernel.Connectors.OpenAI'
    'Microsoft.SemanticKernel.Connectors.AzureOpenAI'
    'Microsoft.SemanticKernel.Yaml'
    'Microsoft.SemanticKernel.Agents.Abstractions'
    'Microsoft.SemanticKernel.Agents.Core'
    'Microsoft.SemanticKernel.Agents.OpenAI'
))

function Get-FormattedValue {
    param (
        [float]$Coverage,
        [bool]$UseIcon = $false
    )
    $formattedNumber = "{0:N1}" -f $Coverage
    $icon = if (-not $UseIcon) { "" } elseif ($Coverage -ge $CoverageThreshold) { '✅' } else { '❌' }
    
    return "$formattedNumber% $icon"
}

$lineCoverage = $jsonContent.summary.linecoverage
$branchCoverage = $jsonContent.summary.branchcoverage

$totalTableData = [PSCustomObject]@{
    'Metric'          = 'Total Coverage'
    'Line Coverage'   = Get-FormattedValue -Coverage $lineCoverage
    'Branch Coverage' = Get-FormattedValue -Coverage $branchCoverage
}

$totalTableData | Format-Table -AutoSize

$assemblyTableData = @()

foreach ($assembly in $jsonContent.coverage.assemblies) {
    $assemblyName = $assembly.name
    $assemblyLineCoverage = $assembly.coverage
    $assemblyBranchCoverage = $assembly.branchcoverage

    $isNonExperimentalAssembly = $nonExperimentalAssemblies -contains $assemblyName

    if ($isNonExperimentalAssembly -and ($assemblyLineCoverage -lt $CoverageThreshold -or $assemblyBranchCoverage -lt $CoverageThreshold)) {
        $coverageBelowThreshold = $true
    }

    $assemblyTableData += [PSCustomObject]@{
        'Assembly Name' = $assemblyName
        'Line'          = Get-FormattedValue -Coverage $assemblyLineCoverage -UseIcon $isNonExperimentalAssembly
        'Branch'        = Get-FormattedValue -Coverage $assemblyBranchCoverage -UseIcon $isNonExperimentalAssembly
    }
}

# Sort in following order:
# Non-experimental assemblies first, sorted by line and then by branch coverage.
# Then experimental assemblies, sorted by line and then by branch coverage.
$sortedTable = $assemblyTableData | Sort-Object {
    $isNonExperimentalAssembly = $nonExperimentalAssemblies -contains $_.'Assembly Name'
    
    $isNonExperimentalAssembly, $_.'Line', $_.'Branch'
} -Descending

$sortedTable | Format-Table -AutoSize

if ($coverageBelowThreshold) {
    Write-Host "Code coverage is lower than defined threshold: $CoverageThreshold. Stopping the task."
    exit 1
}
