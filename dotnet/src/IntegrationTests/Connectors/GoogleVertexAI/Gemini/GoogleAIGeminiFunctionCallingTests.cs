// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.GoogleVertexAI.Gemini;

public sealed class GeminiFunctionCallingTests
{
    private readonly IConfiguration _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    private readonly ITestOutputHelper _output;

    public GeminiFunctionCallingTests(ITestOutputHelper output)
    {
        this._output = output;
    }

    // [Fact(Skip = "This test is for manual verification.")]
    [Fact]
    public async Task EnabledFunctionsShouldReturnFunctionToCallAsync()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>(nameof(CustomerPlugin));
        var sut = new GoogleAIGeminiChatCompletionService(this.GetModel(), this.GetApiKey());
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        var geminiResponse = response as GeminiChatMessageContent;
        Assert.NotNull(geminiResponse);
        Assert.NotNull(geminiResponse.ToolCalls);
        Assert.Single(geminiResponse.ToolCalls, item =>
            item.FullyQualifiedName == $"{nameof(CustomerPlugin)}{GeminiFunction.NameSeparator}{nameof(CustomerPlugin.GetCustomers)}");
    }

    // [Fact(Skip = "This test is for manual verification.")]
    [Fact]
    public async Task AutoInvokeShouldCallFunctionAndReturnResponseAsync()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        var sut = new GoogleAIGeminiChatCompletionService(this.GetModel(), this.GetApiKey());
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this._output.WriteLine(response.Content);
        Assert.Contains("John Kowalski", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Anna Nowak", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Steve Smith", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    public sealed class CustomerPlugin
    {
        [KernelFunction(nameof(GetCustomers))]
        [Description("Get list of customers.")]
        [return: Description("List of customers.")]
        public string[] GetCustomers()
        {
            return new[]
            {
                "John Kowalski",
                "Anna Nowak",
                "Steve Smith",
            };
        }
    }

    private string GetModel() => this._configuration.GetSection("GoogleAI:Gemini:ModelId").Get<string>()!;
    private string GetApiKey() => this._configuration.GetSection("GoogleAI:ApiKey").Get<string>()!;
}
