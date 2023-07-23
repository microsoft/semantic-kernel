@echo off

setlocal

cd %~dp0/nl2sql.console

dotnet restore
dotnet build

cls

dotnet run

endlocal