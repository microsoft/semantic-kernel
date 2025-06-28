// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.Responses;
using OpenAI.VectorStores;
using Plugins;
using Resources;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates how to use tools during a model interaction using <see cref="OpenAIResponseAgent"/>.
/// </summary>
public class Step04_OpenAIResponseAgent_Tools(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task InvokeAgentWithFunctionToolsAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        // Create a plugin that defines the tools to be used by the agent.
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        var tools = plugin.Select(f => f.ToToolDefinition(plugin.Name));
        agent.Kernel.Plugins.Add(plugin);

        ICollection<ChatMessageContent> messages =
        [
            new ChatMessageContent(AuthorRole.User, "What is the special soup and its price?"),
            new ChatMessageContent(AuthorRole.User, "What is the special drink and its price?"),
        ];
        foreach (ChatMessageContent message in messages)
        {
            WriteAgentChatMessage(message);
        }

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(messages);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task InvokeAgentWithWebSearchAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        // ResponseCreationOptions allows you to specify tools for the agent.
        ResponseCreationOptions creationOptions = new();
        creationOptions.Tools.Add(ResponseTool.CreateWebSearchTool());
        OpenAIResponseAgentInvokeOptions invokeOptions = new()
        {
            ResponseCreationOptions = creationOptions,
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync("What was a positive news story from today?", options: invokeOptions);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task InvokeAgentWithFileSearchAsync()
    {
        // Upload a file to the OpenAI File API
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;
        OpenAIFile file = await this.FileClient.UploadFileAsync(stream, filename: "employees.pdf", purpose: FileUploadPurpose.UserData);

        // Create a vector store for the file
        CreateVectorStoreOperation createStoreOp = await this.VectorStoreClient.CreateVectorStoreAsync(
            waitUntilCompleted: true,
            new VectorStoreCreationOptions()
            {
                FileIds = { file.Id },
            });

        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        // ResponseCreationOptions allows you to specify tools for the agent.
        ResponseCreationOptions creationOptions = new();
        creationOptions.Tools.Add(ResponseTool.CreateFileSearchTool([createStoreOp.VectorStoreId], null));
        OpenAIResponseAgentInvokeOptions invokeOptions = new()
        {
            ResponseCreationOptions = creationOptions,
        };

        // Invoke the agent and output the response
        ICollection<ChatMessageContent> messages =
        [
            new ChatMessageContent(AuthorRole.User, "Who is the youngest employee?"),
            new ChatMessageContent(AuthorRole.User, "Who works in sales?"),
            new ChatMessageContent(AuthorRole.User, "I have a customer request, who can help me?"),
        ];
        foreach (ChatMessageContent message in messages)
        {
            WriteAgentChatMessage(message);
        }

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(messages, options: invokeOptions);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }

        // Clean up resources
        RequestOptions noThrowOptions = new() { ErrorOptions = ClientErrorBehaviors.NoThrow };
        this.FileClient.DeleteFile(file.Id, noThrowOptions);
        this.VectorStoreClient.DeleteVectorStore(createStoreOp.VectorStoreId, noThrowOptions);
    }
}
