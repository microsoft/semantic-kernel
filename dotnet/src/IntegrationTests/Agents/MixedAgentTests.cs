// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Assistants;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class MixedAgentTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MixedAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData(false)]
    [InlineData(true)]
    public async Task OpenAIMixedAgentTestAsync(bool useNewFunctionCallingModel)
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        // Arrange, Act & Assert
        await this.VerifyAgentExecutionAsync(
            this.CreateChatCompletionKernel(openAISettings),
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            useNewFunctionCallingModel);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(false)]
    [InlineData(true)]
    public async Task AzureOpenAIMixedAgentAsync(bool useNewFunctionCallingModel)
    {
        AzureOpenAIConfiguration azureOpenAISettings = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;
        Assert.NotNull(azureOpenAISettings);

        // Arrange, Act & Assert
        await this.VerifyAgentExecutionAsync(
            this.CreateChatCompletionKernel(azureOpenAISettings),
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAISettings.Endpoint)),
            azureOpenAISettings.ChatDeploymentName!,
            useNewFunctionCallingModel);
    }

    private async Task VerifyAgentExecutionAsync(
        Kernel chatCompletionKernel,
        OpenAIClientProvider clientProvider,
        string modelName,
        bool useNewFunctionCallingModel)
    {
        // Arrange
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        var executionSettings = useNewFunctionCallingModel ?
            new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() } :
            new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Chat agent doesn't need plug-in since it has access to the shared function result.
        ChatCompletionAgent chatAgent =
            new()
            {
                Name = "Chat",
                Kernel = chatCompletionKernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(executionSettings),
            };
        chatAgent.Kernel.Plugins.Add(plugin);

        // Configure assistant agent with the plugin.
        Assistant definition = await clientProvider.AssistantClient.CreateAssistantAsync(modelName, instructions: "Answer questions about the menu.");
        OpenAIAssistantAgent assistantAgent = new(definition, clientProvider.AssistantClient, [plugin]);

        // Act & Assert
        try
        {
            AgentGroupChat chat = new(chatAgent, assistantAgent);
            await this.AssertAgentInvocationAsync(chat, chatAgent, "What is the special soup?", "Clam Chowder");
            await this.AssertAgentInvocationAsync(chat, assistantAgent, "What is the special drink?", "Chai Tea");
        }
        finally
        {
            await clientProvider.AssistantClient.DeleteAssistantAsync(assistantAgent.Id);
        }
    }

    private async Task AssertAgentInvocationAsync(AgentGroupChat chat, Agent agent, string input, string expected)
    {
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

    private Kernel CreateChatCompletionKernel(AzureOpenAIConfiguration configuration)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: configuration.ChatDeploymentName!,
            endpoint: configuration.Endpoint,
            credentials: new AzureCliCredential());

        return kernelBuilder.Build();
    }

    private Kernel CreateChatCompletionKernel(OpenAIConfiguration configuration)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddOpenAIChatCompletion(
            configuration.ChatModelId!,
            configuration.ApiKey);

        return kernelBuilder.Build();
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
