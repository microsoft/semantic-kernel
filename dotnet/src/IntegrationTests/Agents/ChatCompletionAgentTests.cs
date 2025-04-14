// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class ChatCompletionAgentTests()
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder", false)]
    [InlineData("What is the special soup?", "Clam Chowder", true)]
    public async Task AzureChatCompletionAgentAsync(string input, string expectedAnswerContains, bool useAutoFunctionTermination)
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: configuration.ChatDeploymentName!,
            endpoint: configuration.Endpoint,
            credentials: new AzureCliCredential());

        if (useAutoFunctionTermination)
        {
            this._kernelBuilder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());
        }

        this._kernelBuilder.Plugins.Add(plugin);

        Kernel kernel = this._kernelBuilder.Build();

        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }),
            };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();

        // Assert
        Assert.Single(messages);

        ChatMessageContent response = messages.Single();

        if (useAutoFunctionTermination)
        {
            Assert.Equal(3, history.Length);
            Assert.Single(response.Items.OfType<FunctionResultContent>());
            Assert.Single(response.Items.OfType<TextContent>());
        }
        else
        {
            Assert.Equal(4, history.Length);
            Assert.Single(response.Items);
            Assert.Single(response.Items.OfType<TextContent>());
        }

        Assert.Contains(expectedAnswerContains, messages.Single().Content, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using new function calling model
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder", false)]
    [InlineData("What is the special soup?", "Clam Chowder", true)]
    public async Task AzureChatCompletionAgentUsingNewFunctionCallingModelAsync(string input, string expectedAnswerContains, bool useAutoFunctionTermination)
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: configuration.ChatDeploymentName!,
            endpoint: configuration.Endpoint,
            credentials: new AzureCliCredential());

        if (useAutoFunctionTermination)
        {
            this._kernelBuilder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());
        }

        this._kernelBuilder.Plugins.Add(plugin);

        Kernel kernel = this._kernelBuilder.Build();

        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();

        // Assert
        Assert.Single(messages);

        ChatMessageContent response = messages.Single();

        if (useAutoFunctionTermination)
        {
            Assert.Equal(3, history.Length);
            Assert.Single(response.Items.OfType<FunctionResultContent>());
            Assert.Single(response.Items.OfType<TextContent>());
        }
        else
        {
            Assert.Equal(4, history.Length);
            Assert.Single(response.Items);
            Assert.Single(response.Items.OfType<TextContent>());
        }

        Assert.Contains(expectedAnswerContains, messages.Single().Content, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureChatCompletionStreamingAsync()
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            new AzureCliCredential());

        this._kernelBuilder.Plugins.Add(plugin);

        Kernel kernel = this._kernelBuilder.Build();

        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }),
            };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "What is the special soup?"));

        // Act
        StringBuilder builder = new();
        await foreach (var message in chat.InvokeStreamingAsync(agent))
        {
            builder.Append(message.Content);
        }

        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();

        // Assert
        Assert.Contains("Clam Chowder", builder.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Clam Chowder", history.First().Content, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using new function calling model
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureChatCompletionStreamingUsingNewFunctionCallingModelAsync()
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            new AzureCliCredential());

        this._kernelBuilder.Plugins.Add(plugin);

        Kernel kernel = this._kernelBuilder.Build();

        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Instructions = "Answer questions about the menu.",
                Arguments = new(new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "What is the special soup?"));

        // Act
        StringBuilder builder = new();
        await foreach (var message in chat.InvokeStreamingAsync(agent))
        {
            builder.Append(message.Content);
        }

        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();

        // Assert
        Assert.Contains("Clam Chowder", builder.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Clam Chowder", history.First().Content, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using new function calling model
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AzureChatCompletionDeclarativeAsync()
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            new AzureCliCredential());

        this._kernelBuilder.Plugins.Add(plugin);

        Kernel kernel = this._kernelBuilder.Build();

        var text =
            """
            type: chat_completion_agent
            name: MenuAgent
            description: Answers questions about the menu.
            instructions: Answer questions about the menu.
            tools:
              - id: MenuPlugin.GetSpecials
                type: function
              - id: MenuPlugin.GetItemPrice
                type: function
            """;
        var kernelAgentFactory = new ChatCompletionAgentFactory();

        // Act
        var agent = await kernelAgentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel });
        Assert.NotNull(agent);
        var response = await agent.InvokeAsync("What is the special soup?").FirstAsync();

        // Assert
        Assert.Contains("Clam Chowder", response.Message.Content, StringComparison.OrdinalIgnoreCase);
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

    private sealed class AutoInvocationFilter(bool terminate = true) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await next(context);

            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                context.Terminate = terminate;
            }
        }
    }
}
