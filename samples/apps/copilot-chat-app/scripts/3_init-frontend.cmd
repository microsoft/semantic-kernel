@echo off

cd ..\WebApp

:: Create the .env file
del .\.env
echo REACT_APP_BACKEND_URI=https://localhost:40443/ >> .\.env
if "%2" == "corp" (
    echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47 >> .\.env
)
if "%2" == "msa" (
    echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad >> .\.env
)
if "%2" == "" (
    echo REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common >> .\.env
)
echo REACT_APP_AAD_CLIENT_ID=%1 >> .\.env

:: Build and run the frontend application
yarn install && yarn start