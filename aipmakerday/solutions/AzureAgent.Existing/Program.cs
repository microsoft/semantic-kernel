using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

// Initialize logging
using ILoggerFactory loggerFactory = LoggingServices.CreateLoggerFactory();

// Read configuration settings
FoundrySettings settings = ConfigurationServices.GetFoundrySettings();

// Create the project client, with credential.  Note, can use `AzureCliCredential` with `az login`.
AIProjectClient projectClient = new(settings.ConnectionString, new DefaultAzureCredential());

// Retrieve definition
AgentsClient agentsClient = projectClient.GetAgentsClient();
Agent definition = await agentsClient.GetAgentAsync("<agent-id>");

// Define kernel with logging services
IKernelBuilder builder = Kernel.CreateBuilder();
builder.Services.AddSingleton(loggerFactory);

// Import plugin
builder.Plugins.AddFromType<WorldPlugin>();

// Build kernel
Kernel kernel = builder.Build();

// Create agent
AzureAIAgent agent =
    new(definition, agentsClient)
    {
        Kernel = kernel,
    };

// Start interactive chat
await ChatConsole.ChatAsync(agent);
