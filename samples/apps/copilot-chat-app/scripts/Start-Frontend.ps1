<#
.SYNOPSIS
Builds and runs the Chat Copilot frontend.
#>

Join-Path "$PSScriptRoot" '../webapp' | Set-Location
yarn install
yarn start
