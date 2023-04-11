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