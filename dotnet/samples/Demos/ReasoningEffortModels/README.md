# Reasoning Effort Models Demo

This demo application illustrates how to leverage different reasoning effort levels when using agentic AI with Semantic Kernel. The sample project showcases three distinct agents:

- **Smart Blog Post Agent (Low Reasoning):** Generates an analytical blog post on Semantic Kernel.
- **Poem Agent (Medium Reasoning):** Composes a creative poem about Semantic Kernel.
- **Code Example Agent (High Reasoning):** Provides a sample C# code snippet demonstrating integration with Semantic Kernel.

Each agent uses the `ChatCompletionAgent` with reasoning parameters configured via an extended `AgentBase` class.

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download)
- Valid Azure OpenAI credentials (Deployment Name, Endpoint, and API Key)

## Configuration

The application loads its configuration from either **User Secrets** or **Environment Variables**.

### Using User Secrets (Secret Manager)

**Initialize User Secrets:**
   Open a terminal in the project directory and run:
   ```bash
   dotnet user-secrets init
   ```

Set Your Azure OpenAI Credentials:
Replace the placeholders with your actual credentials:

```
dotnet user-secrets set "AzureOpenAI:DeploymentName" "your-deployment-name"
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://your-resource-name.openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "your-api-key"
```
Note: We are assigning the deployment in the Agent creation, so DeploymentName is not needed. If you add it, it will override the Agent Creation one (used in the AgentBase class constructor)

### Using environment variables

Use these names:

```
# OpenAI
OpenAI__ApiKey

# Azure OpenAI
AzureOpenAI__DeploymentName
AzureOpenAI__Endpoint
AzureOpenAI__ApiKey
```

## Running the Application
1. Set as Default Startup Project:
   - In Visual Studio, right-click the ReasoningEffortModels project in the Solution Explorer and select "Set as Startup Project."
2. Build and Run:
   - Via Visual Studio: Press F5 or click the "Start" button.
   - Via Command Line: Navigate to the project folder and run:
```
dotnet build
dotnet run
```
The console will display the output for each of the three agents, demonstrating how different reasoning effort levels affect the responses.

## Project Structure
- AgentBase.cs: Contains the abstract base class that sets up the Semantic Kernel and configures reasoning effort.
- SmartBlogPostAgent.cs, PoemAgent.cs, CodeExampleAgent.cs: Implementations of agents with different reasoning settings.
- Program.cs: The demo entry point that instantiates each agent and invokes them with sample prompts.
- Options/AzureOpenAIOptions.cs: Holds the configuration options for connecting to Azure OpenAI.