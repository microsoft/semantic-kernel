// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using OllamaSharp;
using Xunit;
using Xunit.Abstractions;
using ChatRole = Microsoft.Extensions.AI.ChatRole;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

public sealed class OllamaChatClientIntegrationTests : IDisposable
{
    private readonly ITestOutputHelper _output;
    private readonly IConfigurationRoot _configuration;

    public OllamaChatClientIntegrationTests(ITestOutputHelper output)
    {
        this._output = output;

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OllamaChatClientIntegrationTests>()
            .Build();
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("phi3")]
    [InlineData("llama3.2")]
    public async Task OllamaChatClientBasicUsageAsync(string modelId)
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        using var ollamaClient = new OllamaApiClient(new Uri(endpoint), modelId);
        var sut = (IChatClient)ollamaClient;

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What is the capital of France? Answer in one word.")
        };

        // Act
        var response = await sut.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        this._output.WriteLine($"Response: {response.Text}");
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("phi3")]
    [InlineData("llama3.2")]
    public async Task OllamaChatClientStreamingUsageAsync(string modelId)
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        using var ollamaClient = new OllamaApiClient(new Uri(endpoint), modelId);
        var sut = (IChatClient)ollamaClient;

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Write a short poem about AI. Keep it under 50 words.")
        };

        // Act
        var responseText = "";
        await foreach (var update in sut.GetStreamingResponseAsync(messages))
        {
            if (update.Text != null)
            {
                responseText += update.Text;
                this._output.WriteLine($"Update: {update.Text}");
            }
        }

        // Assert
        Assert.NotEmpty(responseText);
        this._output.WriteLine($"Complete response: {responseText}");
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("phi3")]
    public async Task OllamaChatClientWithOptionsAsync(string modelId)
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        using var ollamaClient = new OllamaApiClient(new Uri(endpoint), modelId);
        var sut = (IChatClient)ollamaClient;

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Generate a random number between 1 and 10.")
        };

        var chatOptions = new ChatOptions
        {
            Temperature = 0.1f,
            MaxOutputTokens = 50
        };

        // Act
        var response = await sut.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        this._output.WriteLine($"Response: {response.Text}");
    }

    [Fact(Skip = "For manual verification only")]
    public async Task OllamaChatClientServiceCollectionIntegrationAsync()
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        var modelId = "phi3";
        var serviceId = "test-ollama";

        var services = new ServiceCollection();
        services.AddOllamaChatClient(modelId, new Uri(endpoint), serviceId);
        services.AddKernel();

        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>(serviceId);
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What is 2+2? Answer with just the number.")
        };

        var response = await chatClient.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        this._output.WriteLine($"Response: {response.Text}");
    }

    [Fact(Skip = "For manual verification only")]
    public async Task OllamaChatClientKernelBuilderIntegrationAsync()
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        var modelId = "phi3";
        var serviceId = "test-ollama";

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatClient(modelId, new Uri(endpoint), serviceId)
            .Build();

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>(serviceId);
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What is the largest planet in our solar system? Answer in one word.")
        };

        var response = await chatClient.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        this._output.WriteLine($"Response: {response.Text}");
    }

    [Fact(Skip = "For manual verification only")]
    public void OllamaChatClientMetadataTest()
    {
        // Arrange
        var endpoint = "http://localhost:11434";
        var modelId = "phi3";
        using var ollamaClient = new OllamaApiClient(new Uri(endpoint), modelId);
        var sut = (IChatClient)ollamaClient;

        // Act
        var metadata = sut.GetService(typeof(ChatClientMetadata)) as ChatClientMetadata;

        // Assert
        Assert.NotNull(metadata);
        Assert.Equal(modelId, metadata.DefaultModelId);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task OllamaChatClientWithKernelFunctionInvocationAsync()
    {
        // Arrange
        var endpoint = this._configuration.GetSection("Ollama:Endpoint").Get<string>() ?? "http://localhost:11434";
        var modelId = "llama3.2";
        var serviceId = "test-ollama";

        var kernel = Kernel.CreateBuilder()
            .AddOllamaChatClient(modelId, new Uri(endpoint), serviceId)
            .Build();

        // Add a simple function for testing
        kernel.Plugins.AddFromFunctions("TestPlugin", [
            KernelFunctionFactory.CreateFromMethod((string location) =>
                $"The weather in {location} is sunny with 75°F temperature.",
                "GetWeather",
                "Gets the current weather for a location")
        ]);

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>(serviceId);
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What's the weather like in Paris?")
        };

        var response = await chatClient.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        this._output.WriteLine($"Response: {response.Text}");
    }

    public void Dispose()
    {
        // Cleanup if needed
    }
}
