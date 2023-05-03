@echo off

cd ..\WebApp

if "%1" == "" (
    goto :runapp
)

:: Create the .env file
del .\.env
echo REACT_APP_BACKEND_URI=https://localhost:40443/ >> .\.env

if "%2" == "msa" (
    echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad >> .\.env
) else (
    if "%2" == "msft" (
        echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47 >> .\.env
    ) else (
        if "%2" == "" (
            :: if no tenant provided, try using common endpoint
            echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common >> .\.env
        ) else (
            echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/%2 >> .\.env
        )
    )
)
echo REACT_APP_AAD_CLIENT_ID=%1 >> .\.env

:runapp
:: Build and run the frontend application
yarn install && yarn start
