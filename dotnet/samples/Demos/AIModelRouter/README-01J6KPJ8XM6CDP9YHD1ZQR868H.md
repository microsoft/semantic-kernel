---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:56:29Z
---

# AI Model Router

This sample demonstrates how to implement an AI Model Router using Semantic Kernel connectors to direct requests to various AI models based on user input. As part of this example we integrate LMStudio, Ollama, and OpenAI, utilizing the OpenAI Connector for LMStudio and Ollama due to their compatibility with the OpenAI API.

> [!IMPORTANT]
> You can modify to use any other combination of connector or OpenAI compatible API model provider.

## Semantic Kernel Features Used

- [Chat Completion Service](ht*************************************************************************************************************************************cs) - Using the Chat Completion Service [OpenAI Connector implementation](ht****************************************************************************************************************************************cs) to generate responses from the LLM.
- [Filters](ht*************************************************************************************************************************************cs), using to capture selected service and log in the console.

## Prerequisites

- [.NET 8](ht********************************************.0).

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](ht**************************************************************ts) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](ht**************************************************************ts)

```powershell {"id":"01J6KPYX4BC26XACCKK1Q6NTKV"}
# OpenAI (Not required if using Azure OpenAI)
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell {"id":"01J6KPYX4BC26XACCKK2QMWVNY"}
dotnet build
dotnet run
```

### Example of a conversation

> **User** > OpenAI, what is Jupiter? Keep it simple.

> **Assistant** > Sure! Jupiter is the largest planet in our solar system. It's a gas giant, mostly made of hydrogen and helium, and it has a lot of storms, including the famous Great Red Spot. Jupiter also has at least 79 moons.

> **User** > Ollama, what is Jupiter? Keep it simple.

> **Assistant** > Jupiter is a giant planet in our solar system known for being the largest and most massive, famous for its spectacled clouds and dozens of moons including Ganymede which is bigger than Earth!

> **User** > LMStudio, what is Jupiter? Keep it simple.

> **Assistant** > Jupiter is the fifth planet from the Sun in our Solar System and one of its gas giants alongside Saturn, Uranus, and Neptune. It's famous for having a massive storm called the Great Red Spot that has been raging for hundreds of years.