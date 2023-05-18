<#
.SYNOPSIS
Builds and runs the Copilot Chat frontend.
#>

Join-Path "$PSScriptRoot" '../webapp' | Set-Location
yarn install
yarn start
