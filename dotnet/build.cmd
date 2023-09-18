@echo off
setlocal
cd "%~dp0"
dotnet build --configuration Release --interactive ^
  && dotnet test --configuration Release --no-build --no-restore --interactive
