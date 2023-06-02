# Copilot Chat Web App

> This learning sample is for educational purposes only and is not recommended for
production deployments.

See [../README.md](../README.md) for complete instructions on setting up and running the application.

## How to use HTTPS for local development
If you need to run Copilot Chat with HTTPS, you need to create a certificate and sign it with a Certificate Authority (CA) that is trusted locally by your device and browser. You can do that easily with [mkcert](https://github.com/FiloSottile/mkcert#installation).

1. From an elevated shell, run
    ```
    choco install mkcert
    ```
1. Create a new local CA by running
    ```
    mkcert -install
    ```
1. Create a new certificate for all hostnames you wish to run the app on. 
    > It is recommend you do this at the /WebApp directory level. 

    Run
    ```
    mkcert localhost 127.0.0.1 example.test
    ```
    You should see an output that looks like this:
    ```
    Created a new certificate valid for the following names 📜
        - "localhost"
        - "127.0.0.1"
        - "example.test"

    The certificate is at "./localhost+1.pem" and the key at "./localhost+1-key.pem" ✅

    It will expire on 1 September 2025
    ```
1. In the [WebApp .env](./.env) file, uncomment lines 11-13 and populate lines 12 and 13 with the certificate and key files generated in the step above.
    ```
    ...
    # To enable HTTPS, uncomment the following lines
    HTTPS="true"
    SSL_CRT_FILE=localhost+1.pem # Replace with your locally-trusted cert file
    SSL_KEY_FILE=localhost+1-key.pem # Replace with your locally-trusted cert key
    ```
1. In the [webapi appsettings.json](../webapi/appsettings.json) file, find the `"AllowedOrigins"` section, and add the URLs you'll be running the apps on already with `https` prefixed. i.e., from the example hostnames above, the `"AllowedOrigins"` section should look like:
    ```
    ...
    // CORS
    "AllowedOrigins": [
        "http://localhost:3000", 
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        "https://example.test:3000"
    ],
    ...
    ```
1. Add the same URLs (with ports!) as SPA redirect URIs to your AAD app registration. This can be done in Azure Portal ([https://portal.azure.com](https://ms.portal.azure.com/#home)).
1. Restart the `webapi` and `WebApp`, and Copilot Chat should be running locally with HTTPS!


## Authentication

This sample uses the Microsoft Authentication Library (MSAL) for React to authenticate users.
Learn more about it here: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react.

## Debug the web app

Aside from debugging within browsers, you can launch a debug session in Visual Studio.

1. Open the webapp folder (i.e.`/samples/apps/copilot-chat-app/WebApp`) in Visual Studio Code.
2. Go to "Run and Debug" and select on the "Launch Edge against localhost".
> Go [here](https://code.visualstudio.com/docs/typescript/typescript-debugging) to learn more about debugging client-code in Visual Studio Code.

## Serve a production build
By default, we run the app using `yarn start`, which starts a local development server. This enables some additional development behaviors and debuggings features, such as `React.StrictMode`, which will render the app twice to find bugs caused by impure rendering.

If you want to serve a production build of the WebApp (as static files) without any development-specific features,

1. Run  
    ``` 
    yarn build 
    ```
    
    This will generate an optimized and minified production-ready build of the app in the `/build` directory.
2. Once the build is complete, and you have the `/build` directory, run

    ``` 
    yarn serve 
    ```
    
    This will start the server and serve the production build. You should see an output similar to:
    ```
    Serving!                                
    - Local:    http://localhost:3000       
    - Network:  http://192.168.0.100:3000  
    ```