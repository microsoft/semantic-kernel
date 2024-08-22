// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class MixedAgentTests
{
    private const string AssistantModel = "gpt-4o"; // Model must be able to support assistant API
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MixedAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Fact(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    public async Task OpenAIMixedAgentTestAsync()
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        await this.ExecuteAgentAsync(
            this.CreateChatCompletionKernel(openAISettings),
            new(openAISettings.ApiKey),
            AssistantModel);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [Fact]
    public async Task AzureOpenAIMixedAgentAsync()
    {
        AzureOpenAIConfiguration azureOpenAISettings = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;
        Assert.NotNull(azureOpenAISettings);

        await this.ExecuteAgentAsync(
            this.CreateChatCompletionKernel(azureOpenAISettings),
            new(azureOpenAISettings.ApiKey, azureOpenAISettings.Endpoint),
            azureOpenAISettings.ChatDeploymentName!);
    }

    private async Task ExecuteAgentAsync(
        Kernel chatCompletionKernel,
        OpenAIAssistantConfiguration config,
        string modelName)
    {
        // Arrange
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        // Configure chat agent with the plugin.
        ChatCompletionAgent chatAgent =
            new()
            {
                Kernel = chatCompletionKernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }),
            };
        chatAgent.Kernel.Plugins.Add(plugin);

        // Assistant doesn't need plug-in since it has access to the shared function result.
        OpenAIAssistantAgent assistantAgent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config,
                new()
                {
                    Instructions = "Answer questions about the menu.",
                    ModelId = modelName,
                });

        // Act
        try
        {
            AgentGroupChat chat = new(chatAgent, assistantAgent);
            await this.InvokeAgentAsync(chat, chatAgent, "What is the special soup?", "Clam Chowder");
            await this.InvokeAgentAsync(chat, assistantAgent, "What is the special drink?", "Chai Tea");
        }
        finally
        {
            await assistantAgent.DeleteAsync();
        }
    }

    private async Task InvokeAgentAsync(AgentGroupChat chat, Agent agent, string input, string expected)
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
    }

    private Kernel CreateChatCompletionKernel(AzureOpenAIConfiguration configuration)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            configuration.ApiKey);

        return kernelBuilder.Build();
    }

    private Kernel CreateChatCompletionKernel(OpenAIConfiguration configuration)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddOpenAIChatCompletion(
            configuration.ModelId!,
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
