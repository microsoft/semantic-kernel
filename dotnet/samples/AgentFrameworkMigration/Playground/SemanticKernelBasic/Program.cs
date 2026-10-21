// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var client = new PersistentAgentsClient(Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT"), new AzureCliCredential());

// Define the agent
PersistentAgent definition = await client.Administration.CreateAgentAsync(
    Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME"),
    instructions: "You are a coding assistant that always generates code using the code interpreter tool.",
    tools: [new CodeInterpreterToolDefinition()]);

AzureAIAgent agent = new(definition, client);

// Create a thread for the agent conversation.
AgentThread thread = new AzureAIAgentThread(client);

try
{
    await InvokeAgentAsync("Create a python file where it determines the values in the Fibonacci sequence that that are less then the value of 101.");
}
finally
{
    await thread.DeleteAsync();
    await client.Administration.DeleteAgentAsync(agent.Id);
}

async Task InvokeAgentAsync(string input)
{
    ChatMessageContent message = new(AuthorRole.User, input);
    WriteAgentChatMessage(message);

    await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
    {
        WriteAgentChatMessage(response);
    }
}

void WriteAgentChatMessage(ChatMessageContent message)
{
    // Include ChatMessageContent.AuthorName in output, if present.
    string authorExpression = message.Role == AuthorRole.User ? string.Empty : FormatAuthor();
    // Include TextContent (via ChatMessageContent.Content), if present.
    string contentExpression = string.IsNullOrWhiteSpace(message.Content) ? string.Empty : message.Content;
    bool isCode = message.Metadata?.ContainsKey(AzureAIAgent.CodeInterpreterMetadataKey) ?? false;
    string codeMarker = isCode ? "\n  [CODE]\n" : " ";
    Console.WriteLine($"\n# {message.Role}{authorExpression}:{codeMarker}{contentExpression}");

    // Provide visibility for inner content (that isn't TextContent).
    foreach (KernelContent item in message.Items)
    {
        if (item is AnnotationContent annotation)
        {
            if (annotation.Kind == AnnotationKind.UrlCitation)
            {
                Console.WriteLine($"  [{item.GetType().Name}] {annotation.Label}: {annotation.ReferenceId} - {annotation.Title}");
            }
            else
            {
                Console.WriteLine($"  [{item.GetType().Name}] {annotation.Label}: File #{annotation.ReferenceId}");
            }
        }
        else if (item is ActionContent action)
        {
            Console.WriteLine($"  [{item.GetType().Name}] {action.Text}");
        }
        else if (item is ReasoningContent reasoning)
        {
            Console.WriteLine($"  [{item.GetType().Name}] {reasoning.Text ?? "Thinking..."}");
        }
        else if (item is FileReferenceContent fileReference)
        {
            Console.WriteLine($"  [{item.GetType().Name}] File #{fileReference.FileId}");
        }
    }

    if ((message.Metadata?.TryGetValue("Usage", out object? usage) ?? false) && usage is RunStepCompletionUsage agentUsage)
    {
        Console.WriteLine($"  [Usage] Tokens: {agentUsage.TotalTokens}, Input: {agentUsage.PromptTokens}, Output: {agentUsage.CompletionTokens}");
    }

    string FormatAuthor() => message.AuthorName is not null ? $" - {message.AuthorName ?? " * "}" : string.Empty;
}
