param (
    [string]$JsonReportPath,
    [double]$CoverageThreshold
)

$jsonContent = Get-Content $JsonReportPath -Raw | ConvertFrom-Json
$coverageBelowThreshold = $false

function Get-FormattedValue($number) {
    $formattedNumber = "{0:N1}" -f $number
    $icon = if ($number -ge $CoverageThreshold) { '✅' } else { '❌' }
              
    return "$formattedNumber% $icon"
}

$lineCoverage = $jsonContent.summary.linecoverage
$branchCoverage = $jsonContent.summary.branchcoverage

if ($lineCoverage -lt $CoverageThreshold -or $branchCoverage -lt $CoverageThreshold) {
    $coverageBelowThreshold = $true
}

$totalTableData = [PSCustomObject]@{
    'Metric'          = 'Total Coverage'
    'Line Coverage'   = Get-FormattedValue $lineCoverage
    'Branch Coverage' = Get-FormattedValue $branchCoverage
}

$totalTableData | Format-Table -AutoSize

$assemblyTableData = @()

foreach ($assembly in $jsonContent.coverage.assemblies) {
    $assemblyName = $assembly.name
    $assemblyLineCoverage = $assembly.coverage
    $assemblyBranchCoverage = $assembly.branchcoverage

    if ($assemblyLineCoverage -lt $CoverageThreshold -or $assemblyBranchCoverage -lt $CoverageThreshold) {
        $coverageBelowThreshold = $true
    }

    $assemblyTableData += [PSCustomObject]@{
        'Assembly Name' = $assemblyName
        'Line'          = Get-FormattedValue $assemblyLineCoverage
        'Branch'        = Get-FormattedValue $assemblyBranchCoverage
    }
}

$assemblyTableData | Format-Table -AutoSize

if ($coverageBelowThreshold) {
    Write-Host "Code coverage is lower than defined threshold: $CoverageThreshold. Stopping the task."
    exit 1
}
