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
      Write-Host "$_ was changed"

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

if (-not $targets) {
#    $targets = Get-ChildItem $repoRoot -Recurse -Filter *.sln |
#               Select-Object -Expand FullName
  Write-Host "No code changes found"
}

if ($PSVersionTable.PSVersion.Major -ge 7) {
    $targets | ForEach-Object -Parallel {
        param($t) ; Write-Host "  $t" ; dotnet format --verbosity normal $t
    }
} else {
    $jobs = foreach ($t in $targets) {
        Start-Job -ScriptBlock {
            param($target)
            Write-Host "  $target"
            dotnet format --verbosity normal $target
        } -ArgumentList $t
    }

    # wait for all to finish and surface errors
    $jobs | Receive-Job -Wait -AutoRemoveJob
}

popd