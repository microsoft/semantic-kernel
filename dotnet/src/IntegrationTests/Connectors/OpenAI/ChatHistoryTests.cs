// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class ChatHistoryTests(ITestOutputHelper output) : IDisposable
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly XunitLogger<Kernel> _logger = new(output);
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAICompletionTests>()
            .Build();
    private static readonly JsonSerializerOptions s_jsonOptionsCache = new() { WriteIndented = true };

    [Fact]
    public async Task ItSerializesAndDeserializesChatHistoryAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        builder.Plugins.AddFromType<FakePlugin>();
        var kernel = builder.Build();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        ChatHistory history = [];

        // Act
        history.AddUserMessage("Make me a special poem");
        var historyBeforeJson = JsonSerializer.Serialize(history.ToList(), s_jsonOptionsCache);
        var service = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent result = await service.GetChatMessageContentAsync(history, settings, kernel);
        history.AddUserMessage("Ok thank you");

        ChatMessageContent resultOriginalWorking = await service.GetChatMessageContentAsync(history, settings, kernel);
        var historyJson = JsonSerializer.Serialize(history, s_jsonOptionsCache);
        var historyAfterSerialization = JsonSerializer.Deserialize<ChatHistory>(historyJson);
        var exception = await Record.ExceptionAsync(() => service.GetChatMessageContentAsync(historyAfterSerialization!, settings, kernel));

        // Assert
        Assert.Null(exception);
    }

    [Fact]
    public async Task ItUsesChatSystemPromptFromSettingsAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        builder.Plugins.AddFromType<FakePlugin>();
        var kernel = builder.Build();

        string systemPrompt = "You are batman. If asked who you are, say 'I am Batman!'";

        OpenAIPromptExecutionSettings settings = new() { ChatSystemPrompt = systemPrompt };
        ChatHistory history = [];

        // Act
        history.AddUserMessage("Who are you?");
        var service = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent result = await service.GetChatMessageContentAsync(history, settings, kernel);

        // Assert
        Assert.Contains("Batman", result.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItUsesChatSystemPromptFromChatHistoryAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        builder.Plugins.AddFromType<FakePlugin>();
        var kernel = builder.Build();

        string systemPrompt = "You are batman. If asked who you are, say 'I am Batman!'";

        OpenAIPromptExecutionSettings settings = new();
        ChatHistory history = new(systemPrompt);

        // Act
        history.AddUserMessage("Who are you?");
        var service = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent result = await service.GetChatMessageContentAsync(history, settings, kernel);

        // Assert
        Assert.Contains("Batman", result.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    private void ConfigureAzureOpenAIChatAsText(IKernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("Planners:AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }

    public class FakePlugin
    {
        [KernelFunction, Description("creates a special poem")]
        public string CreateSpecialPoem()
        {
            return "ABCDE";
        }
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
        }
    }
}
