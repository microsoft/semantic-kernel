# Semantic Kernel Service - CopilotChat
This ASP.Net web application exposes the Semantic Kernel through a REST-like interface.

# Configure your environment
Before you get started, make sure you have the following requirements in place:
1. [.NET 6.0](https://dotnet.microsoft.com/en-us/download/dotnet/6.0) for building and deploying .NET 6 projects.
1. Update the properties in `./appsettings.json` to configure your Azure OpenAI resource or OpenAI account.
1. Generate and trust a localhost developer certificate.
   - For Windows and Mac run
     ```bash
     dotnet dev-certs https --trust`
     ```
     > Select `Yes` when asked if you want to install this certificate.
   - For Linux run
     ```bash
     dotnet dev-certs https
     ```

   > To verify the certificate has been installed and trusted, run `dotnet run dev-certs https --check`

   > To clean your system of the developer certificate, run `dotnet run dev-certs https --clean`

1. **(Optional)** [Visual Studio Code](http://aka.ms/vscode) or [Visual Studio](http://aka.ms/vsdownload).

# Start the WebApi Service
You can start the WebApi service using the command-line, Visual Studio Code, or Visual Studio.
## Command-line
1. Open a terminal
1. Change directory to the Copilot Chat webapi project directory.
   ```
   cd semantic-kernel/samples/apps/copilot-chat-app/webapi
   ```
1. (Optional) Build the service and verify there are no errors.
   ```
   dotnet build
   ```
1. Run the service
   ```
   dotnet run
   ```
1. Early in the startup, the service will provide a probe endpoint you can use in a web browser to verify
   the service is running.
   ```
   info: Microsoft.SemanticKernel.Kernel[0]
         Health probe: https://localhost:40443/probe
   ```

## Visual Studio Code
1. build (CopilotChatApi)
2. run (CopilotChatApi)
3. [optional] watch (CopilotChatApi)

## Visual Studio (2022 or newer)
1. Open the solution file in Visual Studio 2022 or newer (`semantic-kernel/dotnet/SK-dotnet.sln`).
1. In the solution explorer expand the `samples` folder.
1. Right-click on the `CopilotChatApi` and select `Set as Startup Project`.
1. Start debugging by pressing `F5` or selecting the menu item `Debug`->`Start Debugging`.

# (Optional) Enabling the Qdrant Memory Store
By default, the service uses an in-memory volatile memory store that, when the service stops or restarts, forgets all memories.
[Qdrant](https://github.com/qdrant/qdrant) is a persistent scalable vector search engine that can be deployed locally in a container or [at-scale in the cloud](https://github.com/Azure-Samples/qdrant-azure).

To enable the Qdrant memory store, you must first deploy Qdrant locally and then configure the Copilot Chat API service to use it.

## 1. Configure your environment
Before you get started, make sure you have the following additional requirements in place:
- [Docker Desktop](https://www.docker.com/products/docker-desktop) for hosting the [Qdrant](https://github.com/qdrant/qdrant) vector search engine.

## 2. Deploy Qdrant VectorDB locally
1. Open a terminal and use Docker to pull down the container image.
    ```bash
    docker pull qdrant/qdrant
    ```

1. Change directory to this repo and create a `./data/qdrant` directory to use as persistent storage.
    Then start the Qdrant container on port `6333` using the `./data/qdrant` folder as the persistent storage location.

    ```bash
    cd /src/semantic-kernel
    mkdir ./data/qdrant
    docker run --name copilotchat -p 6333:6333 -v "$(pwd)/data/qdrant:/qdrant/storage" qdrant/qdrant
    ```
    > To stop the container, in another terminal window run `docker container stop copilotchat; docker container rm copilotchat;`.
