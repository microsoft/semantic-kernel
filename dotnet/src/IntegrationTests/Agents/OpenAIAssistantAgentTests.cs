// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
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
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();

        await this.ExecuteStreamingAgentAsync(
            CreateClientProvider(azureOpenAIConfiguration),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding a message with
    /// function result contents.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    [Obsolete("Test is testing obsolete method")]
    public async Task AzureOpenAIAssistantAgentFunctionCallResultAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient);

        AssistantThread thread = await clientProvider.AssistantClient.CreateThreadAsync();
        ChatMessageContent functionResultMessage = new(AuthorRole.Assistant, [new FunctionResultContent("mock-function", result: "A result value")]);
        try
        {
            await agent.AddChatMessageAsync(thread.Id, functionResultMessage);
            var messages = await agent.GetThreadMessagesAsync(thread.Id).ToArrayAsync();
            Assert.Single(messages);
        }
        finally
        {
            await clientProvider.AssistantClient.DeleteThreadAsync(thread.Id);
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    [Obsolete("Test is testing obsolete method")]
    public async Task AzureOpenAIAssistantAgentTokensAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!, instructions: "Repeat the user all of the user messages");
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient)
        {
            RunOptions = new()
            {
                MaxOutputTokenCount = 16,
            }
        };

        AssistantThread thread = await clientProvider.AssistantClient.CreateThreadAsync();
        ChatMessageContent functionResultMessage = new(AuthorRole.User, "A long time ago there lived a king who was famed for his wisdom through all the land. Nothing was hidden from him, and it seemed as if news of the most secret things was brought to him through the air. But he had a strange custom; every day after dinner, when the table was cleared, and no one else was present, a trusty servant had to bring him one more dish. It was covered, however, and even the servant did not know what was in it, neither did anyone know, for the king never took off the cover to eat of it until he was quite alone.");
        try
        {
            await agent.AddChatMessageAsync(thread.Id, functionResultMessage);
            await Assert.ThrowsAsync<KernelException>(() => agent.InvokeAsync(thread.Id).ToArrayAsync().AsTask());
        }
        finally
        {
            await clientProvider.AssistantClient.DeleteThreadAsync(thread.Id);
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding additional messages to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentWithThreadCustomOptionsAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient);

        ThreadCreationOptions threadOptions = new()
        {
            InitialMessages =
            {
                new ChatMessageContent(AuthorRole.User, "Hello").ToThreadInitializationMessage(),
                new ChatMessageContent(AuthorRole.User, "How may I help you?").ToThreadInitializationMessage(),
            }
        };
        OpenAIAssistantAgentThread agentThread = new(clientProvider.AssistantClient, threadOptions);

        try
        {
            var originalMessages = await agentThread.GetMessagesAsync().ToArrayAsync();
            Assert.Equal(2, originalMessages.Length);

            RunCreationOptions invocationOptions = new()
            {
                AdditionalMessages = {
                    new ChatMessageContent(AuthorRole.User, "This is my real question...in three parts:").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 1").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 2").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 3").ToThreadInitializationMessage(),
                }
            };

            var responseMessages = await agent.InvokeAsync([], agentThread, options: new() { RunCreationOptions = invocationOptions }).ToArrayAsync();
            Assert.Single(responseMessages);

            var finalMessages = await agentThread.GetMessagesAsync().ToArrayAsync();
            Assert.Equal(7, finalMessages.Length);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding additional message to a thread.
    /// function result contents.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    [Obsolete("Test is testing obsolete method")]
    public async Task AzureOpenAIAssistantAgentAdditionalMessagesAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient);

        ThreadCreationOptions threadOptions = new()
        {
            InitialMessages =
            {
                new ChatMessageContent(AuthorRole.User, "Hello").ToThreadInitializationMessage(),
                new ChatMessageContent(AuthorRole.User, "How may I help you?").ToThreadInitializationMessage(),
            }
        };
        AssistantThread thread = await clientProvider.AssistantClient.CreateThreadAsync(threadOptions);
        try
        {
            var messages = await agent.GetThreadMessagesAsync(thread.Id).ToArrayAsync();
            Assert.Equal(2, messages.Length);

            RunCreationOptions invocationOptions = new()
            {
                AdditionalMessages = {
                    new ChatMessageContent(AuthorRole.User, "This is my real question...in three parts:").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 1").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 2").ToThreadInitializationMessage(),
                    new ChatMessageContent(AuthorRole.User, "Part 3").ToThreadInitializationMessage(),
                }
            };

            messages = await agent.InvokeAsync(thread.Id, invocationOptions).ToArrayAsync();
            Assert.Single(messages);

            messages = await agent.GetThreadMessagesAsync(thread.Id).ToArrayAsync();
            Assert.Equal(7, messages.Length);
        }
        finally
        {
            await clientProvider.AssistantClient.DeleteThreadAsync(thread.Id);
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Fact]
    [Obsolete("Test is testing obsolete method")]
    public async Task AzureOpenAIAssistantAgentStreamingFileSearchAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient);

        // Upload file - Using a table of fictional employees.
        OpenAIFileClient fileClient = clientProvider.Client.GetOpenAIFileClient();
        await using Stream stream = File.OpenRead("TestData/employees.pdf")!;
        OpenAIFile fileInfo = await fileClient.UploadFileAsync(stream, "employees.pdf", FileUploadPurpose.Assistants);

        // Create a vector-store
        VectorStoreClient vectorStoreClient = clientProvider.Client.GetVectorStoreClient();
        CreateVectorStoreOperation result =
            await vectorStoreClient.CreateVectorStoreAsync(waitUntilCompleted: false,
                new VectorStoreCreationOptions()
                {
                    FileIds = { fileInfo.Id }
                });

        AssistantThread thread = await clientProvider.AssistantClient.CreateThreadAsync();
        try
        {
            await agent.AddChatMessageAsync(thread.Id, new(AuthorRole.User, "Who works in sales?"));
            ChatHistory messages = [];
            var chunks = await agent.InvokeStreamingAsync(thread.Id, messages: messages).ToArrayAsync();
            Assert.NotEmpty(chunks);
            Assert.Single(messages);
        }
        finally
        {
            await clientProvider.AssistantClient.DeleteThreadAsync(thread.Id);
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
            await vectorStoreClient.DeleteVectorStoreAsync(result.VectorStoreId);
            await fileClient.DeleteFileAsync(fileInfo.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentWithThreadCustomOptionsStreamingAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient);

        OpenAIAssistantAgentThread agentThread = new(clientProvider.AssistantClient);

        try
        {
            RunCreationOptions invocationOptions = new()
            {
                InstructionsOverride = "Respond to all user questions with 'Computer says no'.",
            };

            var message = new ChatMessageContent(AuthorRole.User, "What is the capital of France?");
            var responseMessages = await agent.InvokeStreamingAsync(
                message,
                agentThread,
                new OpenAIAssistantAgentInvokeOptions() { RunCreationOptions = invocationOptions }).ToArrayAsync();
            var responseText = string.Join(string.Empty, responseMessages.Select(x => x.Message.Content));

            Assert.Contains("Computer says no", responseText);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> created declaratively.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentDeclarativeAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClientProvider clientProvider = CreateClientProvider(azureOpenAIConfiguration);

        var text =
            $"""
            type: openai_assistant
            name: MyAgent
            description: My helpful agent.
            instructions: You are helpful agent.
            model:
              id: {azureOpenAIConfiguration.ChatDeploymentName}
              connection:
                type: azure_openai
                endpoint: {azureOpenAIConfiguration.Endpoint}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<TokenCredential>(new AzureCliCredential());
        var kernel = builder.Build();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel });
        Assert.NotNull(agent);

        OpenAIAssistantAgentThread agentThread = new(clientProvider.AssistantClient);
        try
        {
            RunCreationOptions invocationOptions = new()
            {
                InstructionsOverride = "Respond to all user questions with 'Computer says no'.",
            };

            var response = await agent.InvokeAsync(
                "What is the capital of France?",
                agentThread,
                new OpenAIAssistantAgentInvokeOptions() { RunCreationOptions = invocationOptions }).FirstAsync();

            Assert.Contains("Computer says no", response.Message.Content);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    private async Task ExecuteAgentAsync(
        OpenAIClientProvider clientProvider,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(modelName, instructions: "Answer questions about the menu.");
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient, [plugin]);

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
            await clientProvider.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIClientProvider clientProvider,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(modelName, instructions: "Answer questions about the menu.");
        OpenAIAssistantAgent agent = new(definition, clientProvider.AssistantClient, [plugin]);

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

    private AzureOpenAIConfiguration ReadAzureConfiguration()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        return azureOpenAIConfiguration;
    }

    private static OpenAIClientProvider CreateClientProvider(AzureOpenAIConfiguration azureOpenAIConfiguration)
    {
        return OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint));
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
