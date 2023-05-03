@echo off

:: Generate and trust a localhost developer certificate
dotnet dev-certs https --trust

cd ..\webapi

:: If key provided, store it in user secrets
if not "%1" == "" (
    dotnet user-secrets set "Completion:Key" "%1"
    dotnet user-secrets set "Embedding:Key" "%1"
)

:: Build and run the backend API server
dotnet build && dotnet run
