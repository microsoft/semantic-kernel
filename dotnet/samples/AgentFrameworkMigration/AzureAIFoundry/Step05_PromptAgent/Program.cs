// Copyright (c) Microsoft. All rights reserved.

// This sample shows how to migrate a Semantic Kernel AzureAIAgent, which uses a server-side agent definition
// and a server-side thread, to an Agent Framework Microsoft Foundry Prompt Agent, which uses a server-side
// versioned agent definition and a server-side conversation.
// Use the same Agent Framework pattern to replace OpenAIAssistantAgent, because the OpenAI Assistants API is shut down.

using Azure.AI.Agents.Persistent;
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Foundry;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var azureEndpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT") ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
// The classic Foundry Agents service used by the SK AzureAIAgent rejects the top_p parameter it sends to GPT-5.6 models, so default to gpt-5.4-mini.
var deploymentName = System.Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME") ?? "gpt-5.4-mini";
const string AgentName = "MigrationPromptAgent";
const string AgentInstructions = "You are good at telling jokes.";
var userInput = "Tell me a joke about a pirate.";
var followUpInput = "Now explain why the joke is funny in one sentence.";

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var azureAgentClient = AzureAIAgent.CreateAgentsClient(azureEndpoint, new AzureCliCredential());

    // SK creates the server-side agent definition with the Persistent Agents client.
    PersistentAgent definition = await azureAgentClient.Administration.CreateAgentAsync(
        deploymentName,
        name: AgentName,
        instructions: AgentInstructions);

    AzureAIAgent agent = new(definition, azureAgentClient);

    // SK callers create the provider-specific server-side thread themselves.
    var thread = new AzureAIAgentThread(azureAgentClient);

    try
    {
        await foreach (var item in agent.InvokeAsync(userInput, thread))
        {
            Console.WriteLine(item.Message);
        }

        Console.WriteLine("---");
        await foreach (StreamingChatMessageContent update in agent.InvokeStreamingAsync(followUpInput, thread))
        {
            Console.Write(update);
        }

        Console.WriteLine();
    }
    finally
    {
        // SK threads delete themselves; the agent definition is deleted through the client.
        await thread.DeleteAsync();
        await azureAgentClient.Administration.DeleteAgentAsync(agent.Id);
    }
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent (Microsoft Foundry Prompt Agent) ===\n");

    AIProjectClient projectClient = new(new Uri(azureEndpoint), new AzureCliCredential());

    // AF creates the server-side Prompt Agent as a versioned definition in the Foundry project.
    ProjectsAgentVersion agentVersion = await projectClient.AgentAdministrationClient.CreateAgentVersionAsync(
        AgentName,
        new ProjectsAgentVersionCreationOptions(
            new DeclarativeAgentDefinition(model: deploymentName)
            {
                Instructions = AgentInstructions,
            }));

    FoundryAgent agent = projectClient.AsAIAgent(agentVersion);

    // The agent creates the server-side conversation; there is no provider-specific thread type to construct.
    ChatClientAgentSession session = await agent.CreateConversationSessionAsync();

    try
    {
        Console.WriteLine(await agent.RunAsync(userInput, session));

        Console.WriteLine("---");
        await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(followUpInput, session))
        {
            Console.Write(update);
        }

        Console.WriteLine();

        // An existing Prompt Agent is loaded by name instead of by the Persistent Agents id.
        Console.WriteLine("\n=== AF Agent (existing Prompt Agent loaded by name) ===\n");
        ProjectsAgentRecord agentRecord = await projectClient.AgentAdministrationClient.GetAgentAsync(AgentName);
        FoundryAgent existingAgent = projectClient.AsAIAgent(agentRecord);
        Console.WriteLine(await existingAgent.RunAsync(userInput));
    }
    finally
    {
        // AgentSession has no delete API, so the caller deletes the server-side conversation through the provider SDK.
        // Deleting the agent removes the Prompt Agent and all of its versions.
        await projectClient.GetProjectOpenAIClient().GetProjectConversationsClient().DeleteConversationAsync(session.ConversationId);
        await projectClient.AgentAdministrationClient.DeleteAgentAsync(AgentName);
    }
}
