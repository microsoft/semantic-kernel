# Semantic Kernel Service - CopilotChat

## Introduction
This ASP.Net web API application exposes the functionalities of the Semantic Kernel online through a REST interface.

## Configuration
Populate the settings in the file found at **..\semantic-kernel\samples\apps\copilot-chat-app\webapi\appsettings.json**

## Building and Running the Service
To build and run the service, you can use Visual Studio, or simply the dotnet build tools.

### Visual Studio
- Open **..\semantic-kernel\dotnet\SK-dotnet.sln**
- In the solution explorer, go in the samples folder, then right-click on CopilotChatApi
- On the pop-up menu that appears, select "Set as Startup Project"
- Press F5

### dotnet Build Tools
- cd into **..\semantic-kernel\samples\apps\copilot-chat-app\webapi\\**
- Enter **dotnet run**

## Enabling the Qdrant Memory Store (Optional)
By default, the Copilot Chat API services uses an in-memory volatile memory store that, when the service stops or restarts, forgets all memories.
[Qdrant](https://github.com/qdrant/qdrant) is a persistent scalable vector search engine that can be deployed locally in a container or [at-scale in the cloud](https://github.com/Azure-Samples/qdrant-azure).

To enable the Qdrant memory store, you must first deploy Qdrant locally and then configure the Copilot Chat API service to use it.

#### 1. Configure your environment
Before you get started, make sure you have the following additional requirements in place:
- [Docker Desktop](https://www.docker.com/products/docker-desktop) for hosting the [Qdrant](https://github.com/qdrant/qdrant) vector search engine.

#### 2. Deploy Qdrant VectorDB locally 
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