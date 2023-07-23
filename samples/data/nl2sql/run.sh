#!/usr/bin/env bash

set -e

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/nl2sql.console"

dotnet restore
dotnet build

tput reset

dotnet run
