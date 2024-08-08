// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class ChatCompletionAgentTests(ITestOutputHelper output) : IDisposable
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="ChatCompletionAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [Theory]
    [InlineData("What is the special soup?", "Clam Chowder", false)]
    [InlineData("What is the special soup?", "Clam Chowder", true)]
    public async Task AzureChatCompletionAgentAsync(string input, string expectedAnswerContains, bool useAutoFunctionTermination)
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            configuration.ApiKey);

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

    private readonly XunitLogger<Kernel> _logger = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);

    public void Dispose()
    {
        this._logger.Dispose();
        this._testOutputHelper.Dispose();
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
