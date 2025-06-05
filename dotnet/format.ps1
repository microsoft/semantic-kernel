$ErrorActionPreference = 'Stop'

# --- config -------------------------------------------------------
$exclude = @(
  'Experimental.Orchestration.Flow.csproj',
  'Experimental.Orchestration.Flow.UnitTests.csproj',
  'Experimental.Orchestration.Flow.IntegrationTests.csproj'
)
$repoRoot = (git rev-parse --show-toplevel).Trim()
$repoRoot = (Resolve-Path $repoRoot).Path       # canonical form
pushd $repoRoot
# -----------------------------------------------------------------

$targets =
  git diff --name-only main..HEAD |
  ForEach-Object {
      $dir = Split-Path (Join-Path $repoRoot $_) -Parent   # << absolute
      while ($dir -and $dir -ne $repoRoot) {
          $proj = Get-ChildItem -LiteralPath $dir -Filter *.csproj -File -ErrorAction Ignore |
                  Select-Object -First 1

          if ($proj) {
              if ($exclude -notcontains $proj.Name) { $proj.FullName }
              break
          }
          $dir = Split-Path $dir -Parent
      }
  } |
  Sort-Object -Unique

popd

if (-not $targets) {
#    $targets = Get-ChildItem $repoRoot -Recurse -Filter *.slnx |
#               Select-Object -Expand FullName
  Write-Host "No code changes found"
}

foreach ($t in $targets) {
    Write-Host "Formatting $t"
}

foreach ($t in $targets) {
    dotnet format --no-restore --verbosity diag $t
}
