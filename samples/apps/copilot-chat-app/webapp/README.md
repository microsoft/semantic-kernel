# Copilot Chat Web App

> This learning sample is for educational purposes only and is not recommended for
production deployments.

See [../README.md](../README.md) for complete instructions on setting up and running the application.

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