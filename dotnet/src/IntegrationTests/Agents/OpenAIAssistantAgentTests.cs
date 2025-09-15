// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Assistants;
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
            OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(openAISettings.ApiKey)),
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

        OpenAIClient client = CreateClient(azureOpenAIConfiguration);
        AssistantClient assistantClient = client.GetAssistantClient();

        await this.ExecuteAgentAsync(
            CreateClient(azureOpenAIConfiguration),
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
            OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(openAISettings.ApiKey)),
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
            CreateClient(azureOpenAIConfiguration),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding additional messages to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentWithThreadCustomOptionsAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClient client = CreateClient(azureOpenAIConfiguration);
        AssistantClient assistantClient = client.GetAssistantClient();
        Assistant definition = await assistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, assistantClient);

        ThreadCreationOptions threadOptions = new()
        {
            InitialMessages =
            {
                new ChatMessageContent(AuthorRole.User, "Hello").ToThreadInitializationMessage(),
                new ChatMessageContent(AuthorRole.User, "How may I help you?").ToThreadInitializationMessage(),
            }
        };
        OpenAIAssistantAgentThread agentThread = new(assistantClient, threadOptions);

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
            await assistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentWithThreadCustomOptionsStreamingAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClient client = CreateClient(azureOpenAIConfiguration);
        AssistantClient assistantClient = client.GetAssistantClient();
        Assistant definition = await assistantClient.CreateAssistantAsync(azureOpenAIConfiguration.ChatDeploymentName!);
        OpenAIAssistantAgent agent = new(definition, assistantClient);

        OpenAIAssistantAgentThread agentThread = new(assistantClient);

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
            await assistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> created declaratively.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureOpenAIAssistantAgentDeclarativeAsync()
    {
        AzureOpenAIConfiguration azureOpenAIConfiguration = this.ReadAzureConfiguration();
        OpenAIClient client = CreateClient(azureOpenAIConfiguration);
        AssistantClient assistantClient = client.GetAssistantClient();

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

        OpenAIAssistantAgentThread agentThread = new(assistantClient);
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
            await assistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    private async Task ExecuteAgentAsync(
        OpenAIClient client,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        AssistantClient assistantClient = client.GetAssistantClient();
        Assistant definition = await client.GetAssistantClient().CreateAssistantAsync(modelName, instructions: "Answer questions about the menu.");
        OpenAIAssistantAgent agent = new(definition, assistantClient, [plugin]);

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
            await assistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIClient client,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        AssistantClient assistantClient = client.GetAssistantClient();
        Assistant definition = await assistantClient.CreateAssistantAsync(modelName, instructions: "Answer questions about the menu.");
        OpenAIAssistantAgent agent = new(definition, assistantClient, [plugin]);

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

    private static AzureOpenAIClient CreateClient(AzureOpenAIConfiguration azureOpenAIConfiguration)
    {
        return OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint));
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
