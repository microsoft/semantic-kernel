// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIAssistantAgentTests(ITestOutputHelper output) : IDisposable
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
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
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        await this.ExecuteAgentAsync(
            new(openAIConfiguration.ApiKey),
            openAIConfiguration.ModelId,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [Theory(Skip = "No supported endpoint configured.")]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteAgentAsync(
            new(azureOpenAIConfiguration.ApiKey, azureOpenAIConfiguration.Endpoint),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    private async Task ExecuteAgentAsync(
        OpenAIAssistantConfiguration config,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);

        Kernel kernel = this._kernelBuilder.Build();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel,
                config,
                new()
                {
                    Instructions = "Answer questions about the menu.",
                    ModelId = modelName,
                });

        AgentGroupChat chat = new();
        chat.Add(new ChatMessageContent(AuthorRole.User, input));

        // Act
        StringBuilder builder = new();
        await foreach (var message in chat.InvokeAsync(agent))
        {
            builder.Append(message.Content);
        }

        // Assert
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
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
}
