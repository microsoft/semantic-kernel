// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.VectorStores;
using Resources;

namespace GettingStarted;

/// <summary>
/// These examples demonstrates the <see cref="OpenAIAssistantAgent"/>
/// </summary>
public class Step8_OpenAIAssistant(ITestOutputHelper output) : BaseTest(output)
{
    protected override bool ForceOpenAI => true;

    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    /// <summary>
    /// This example shows how to initialize a <see cref="OpenAIAssistantAgent"/> and
    /// perform basic Agent functionality.
    /// </summary>
    [Fact]
    public async Task UseSingleOpenAIAssistantAgentAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: GetOpenAIConfiguration(),
                new()
                {
                    Instructions = HostInstructions,
                    Name = HostName,
                    ModelId = this.Model,
                });

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent interaction.
        string threadId = await agent.CreateThreadAsync();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup?");
            await InvokeAgentAsync("What is the special drink?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            await agent.AddChatMessageAsync(threadId, new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (ChatMessageContent content in agent.InvokeAsync(threadId))
            {
                if (content.Role != AuthorRole.Tool)
                {
                    Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
                }
            }
        }
    }

    /// <summary>
    /// This example shows how to provide files to a <see cref="OpenAIAssistantAgent"/> 
    /// so that you can provide grounding context i.e. Retrieval Augmented Generation.
    /// </summary>
    [Fact]
    public async Task UseSingleOpenAIAssistantAgentWithFileAsync()
    {
        OpenAIServiceConfiguration config = GetOpenAIConfiguration();

        FileClient fileClient = config.CreateFileClient();

        OpenAIFileInfo uploadFile =
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("semantic-kernel.pdf")!),
                "semantic-kernel.pdf",
                FileUploadPurpose.Assistants);

        VectorStoreClient vectorStoreClient = config.CreateVectorStoreClient();
        VectorStoreCreationOptions vectorStoreOptions =
            new()
            {
                FileIds = [uploadFile.Id]
            };
        VectorStore vectorStore = await vectorStoreClient.CreateVectorStoreAsync(vectorStoreOptions);

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: config,
                new()
                {
                    Instructions = HostInstructions,
                    Name = HostName,
                    ModelId = this.Model,
                    VectorStoreId = vectorStore.Id,
                });

        // Create a thread for the agent interaction.
        string threadId = await agent.CreateThreadAsync();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the Semantic Kernel?");
            await InvokeAgentAsync("Can I create agents the Semantic Kernel?");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            await agent.AddChatMessageAsync(threadId, new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (ChatMessageContent content in agent.InvokeAsync(threadId))
            {
                if (content.Role != AuthorRole.Tool)
                {
                    Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
                }
            }
        }
    }

    /// <summary>
    /// This example shows how use code interpreter a <see cref="OpenAIAssistantAgent"/> 
    /// so that you can perform complex operations.
    /// </summary>
    [Fact]
    public async Task UseSingleOpenAIAssistantAgentWithCodeInterpreterAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: GetOpenAIConfiguration(),
                new()
                {
                    Instructions = HostInstructions,
                    Name = HostName,
                    ModelId = this.Model,
                });

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent interaction.
        string threadId = await agent.CreateThreadAsync();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup?");
            await InvokeAgentAsync("What is the special drink?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            await agent.AddChatMessageAsync(threadId, new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (ChatMessageContent content in agent.InvokeAsync(threadId))
            {
                if (content.Role != AuthorRole.Tool)
                {
                    Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
                }
            }
        }
    }

    private OpenAIServiceConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIServiceConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIServiceConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));

    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials()
        {
            return @"
Special Soup: Clam Chowder
Special Salad: Cobb Salad
Special Drink: Chai Tea
";
        }

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem)
        {
            return "$9.99";
        }
    }
}
