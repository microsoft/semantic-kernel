@echo off

:: Generate and trust a localhost developer certificate
dotnet dev-certs https --trust

cd ..\webapi

:: Build and run the backend API server
dotnet build && dotnet run