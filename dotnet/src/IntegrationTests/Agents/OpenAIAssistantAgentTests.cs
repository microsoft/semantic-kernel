// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.VectorStores;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIAssistantAgentTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task OpenAIAssistantAgentTestAsync(string input, string expectedAnswerContains)
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        await this.ExecuteAgentAsync(
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteAgentAsync(
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task OpenAIAssistantAgentStreamingAsync(string input, string expectedAnswerContains)
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        await this.ExecuteStreamingAgentAsync(
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ModelId,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentStreamingAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteStreamingAgentAsync(
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding a message with
    /// function result contents.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentFunctionCallResultAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
                new(azureOpenAIConfiguration.ChatDeploymentName!),
                new Kernel());

        string threadId = await agent.CreateThreadAsync();
        ChatMessageContent functionResultMessage = new(AuthorRole.Assistant, [new FunctionResultContent("mock-function", result: "A result value")]);
        try
        {
            await agent.AddChatMessageAsync(threadId, functionResultMessage);
            var messages = await agent.GetThreadMessagesAsync(threadId).ToArrayAsync();
            Assert.Single(messages);
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentTokensAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
                new(azureOpenAIConfiguration.ChatDeploymentName!)
                {
                    Instructions = "Repeat the user all of the user messages",
                    ExecutionOptions = new()
                    {
                        MaxCompletionTokens = 16,
                    }
                },
                new Kernel());

        string threadId = await agent.CreateThreadAsync();
        ChatMessageContent functionResultMessage = new(AuthorRole.User, "A long time ago there lived a king who was famed for his wisdom through all the land. Nothing was hidden from him, and it seemed as if news of the most secret things was brought to him through the air. But he had a strange custom; every day after dinner, when the table was cleared, and no one else was present, a trusty servant had to bring him one more dish. It was covered, however, and even the servant did not know what was in it, neither did anyone know, for the king never took off the cover to eat of it until he was quite alone.");
        try
        {
            await agent.AddChatMessageAsync(threadId, functionResultMessage);
            await Assert.ThrowsAsync<KernelException>(() => agent.InvokeAsync(threadId).ToArrayAsync().AsTask());
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding additional message to a thread.
    /// function result contents.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentAdditionalMessagesAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
                new(azureOpenAIConfiguration.ChatDeploymentName!),
                new Kernel());

        OpenAIThreadCreationOptions threadOptions = new()
        {
            Messages = [
                new ChatMessageContent(AuthorRole.User, "Hello"),
                new ChatMessageContent(AuthorRole.Assistant, "How may I help you?"),
            ]
        };
        string threadId = await agent.CreateThreadAsync(threadOptions);
        try
        {
            var messages = await agent.GetThreadMessagesAsync(threadId).ToArrayAsync();
            Assert.Equal(2, messages.Length);

            OpenAIAssistantInvocationOptions invocationOptions = new()
            {
                AdditionalMessages = [
                    new ChatMessageContent(AuthorRole.User, "This is my real question...in three parts:"),
                    new ChatMessageContent(AuthorRole.User, "Part 1"),
                    new ChatMessageContent(AuthorRole.User, "Part 2"),
                    new ChatMessageContent(AuthorRole.User, "Part 3"),
                ]
            };

            messages = await agent.InvokeAsync(threadId, invocationOptions).ToArrayAsync();
            Assert.Single(messages);

            messages = await agent.GetThreadMessagesAsync(threadId).ToArrayAsync();
            Assert.Equal(7, messages.Length);
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Fact]
    public async Task AzureOpenAIAssistantAgentStreamingFileSearchAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        OpenAIClientProvider provider = OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint));
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                provider,
                new(azureOpenAIConfiguration.ChatDeploymentName!),
                new Kernel());

        // Upload file - Using a table of fictional employees.
        OpenAIFileClient fileClient = provider.Client.GetOpenAIFileClient();
        await using Stream stream = File.OpenRead("TestData/employees.pdf")!;
        OpenAIFile fileInfo = await fileClient.UploadFileAsync(stream, "employees.pdf", FileUploadPurpose.Assistants);

        // Create a vector-store
        VectorStoreClient vectorStoreClient = provider.Client.GetVectorStoreClient();
        CreateVectorStoreOperation result =
            await vectorStoreClient.CreateVectorStoreAsync(waitUntilCompleted: false,
                new VectorStoreCreationOptions()
                {
                    FileIds = { fileInfo.Id }
                });

        string threadId = await agent.CreateThreadAsync();
        try
        {
            await agent.AddChatMessageAsync(threadId, new(AuthorRole.User, "Who works in sales?"));
            ChatHistory messages = [];
            var chunks = await agent.InvokeStreamingAsync(threadId, messages: messages).ToArrayAsync();
            Assert.NotEmpty(chunks);
            Assert.Single(messages);
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
            await vectorStoreClient.DeleteVectorStoreAsync(result.VectorStoreId);
            await fileClient.DeleteFileAsync(fileInfo.Id);
        }
    }

    private async Task ExecuteAgentAsync(
        OpenAIClientProvider config,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
                },
                kernel);

        try
        {
            AgentGroupChat chat = new();
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Act
            StringBuilder builder = new();
            await foreach (var message in chat.InvokeAsync(agent))
            {
                builder.Append(message.Content);
            }

            // Assert
            Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
            await foreach (var message in chat.GetChatMessagesAsync())
            {
                AssertMessageValid(message);
            }
        }
        finally
        {
            await agent.DeleteAsync();
        }
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIClientProvider config,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
                },
                kernel);

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

        // Act
        StringBuilder builder = new();
        await foreach (var message in chat.InvokeStreamingAsync(agent))
        {
            builder.Append(message.Content);
        }

        // Assert
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expected, history.First().Content, StringComparison.OrdinalIgnoreCase);
    }

    private static void AssertMessageValid(ChatMessageContent message)
    {
        if (message.Items.OfType<FunctionResultContent>().Any())
        {
            Assert.Equal(AuthorRole.Tool, message.Role);
            return;
        }

        if (message.Items.OfType<FunctionCallContent>().Any())
        {
            Assert.Equal(AuthorRole.Assistant, message.Role);
            return;
        }

        Assert.Equal(string.IsNullOrEmpty(message.AuthorName) ? AuthorRole.User : AuthorRole.Assistant, message.Role);
    }

    public sealed class MenuPlugin
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
