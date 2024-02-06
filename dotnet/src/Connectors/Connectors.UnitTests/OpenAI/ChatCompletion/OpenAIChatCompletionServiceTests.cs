// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletion;

/// <summary>
/// Unit tests for <see cref="OpenAIChatCompletionService"/>
/// </summary>
public sealed class OpenAIChatCompletionServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly OpenAIFunction _timepluginDate, _timepluginNow;
    private readonly OpenAIPromptExecutionSettings _executionSettings;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAIChatCompletionServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();

        IList<KernelFunctionMetadata> functions = KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string? format = null) => DateTime.Now.Date.ToString(format, CultureInfo.InvariantCulture), "Date", "TimePlugin.Date"),
            KernelFunctionFactory.CreateFromMethod((string? format = null) => DateTime.Now.ToString(format, CultureInfo.InvariantCulture), "Now", "TimePlugin.Now"),
        }).GetFunctionsMetadata();

        this._timepluginDate = functions[0].ToOpenAIFunction();
        this._timepluginNow = functions[1].ToOpenAIFunction();

        this._executionSettings = new()
        {
            ToolCallBehavior = ToolCallBehavior.EnableFunctions(new[] { this._timepluginDate, this._timepluginNow })
        };
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIChatCompletionService("model-id", "api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIChatCompletionService("model-id", "api-key", "organization");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient("key");
        var service = includeLoggerFactory ?
            new OpenAIChatCompletionService("model-id", client, loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIChatCompletionService("model-id", client);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionToolCallsWhenUsingAutoAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(new ChatHistory(), this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(2, optionsJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("TimePlugin-Date", optionsJson.GetProperty("tools")[0].GetProperty("function").GetProperty("name").GetString());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("tools")[1].GetProperty("function").GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionToolCallsWhenUsingNowAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._executionSettings.ToolCallBehavior = ToolCallBehavior.RequireFunction(this._timepluginNow);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(new ChatHistory(), this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("tools")[0].GetProperty("function").GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesNoFunctionsWhenUsingNoneAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._executionSettings.ToolCallBehavior = null;

        // Act
        await chatCompletion.GetChatMessageContentsAsync(new ChatHistory(), this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.False(optionsJson.TryGetProperty("functions", out var _));
    }

    [Fact]
    public async Task ItAddsIdToChatMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello", metadata: new Dictionary<string, object?>() { { OpenAIChatMessageContent.ToolIdProperty, "John Doe" } });

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(2, optionsJson.GetProperty("messages").GetArrayLength());
        Assert.Equal("John Doe", optionsJson.GetProperty("messages")[1].GetProperty("tool_call_id").GetString());
    }

    [Fact]
    public async Task ItGetChatMessageContentsShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(AzureChatCompletionResponse, Encoding.UTF8, "application/json") };

        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        var chatMessage = await chatCompletion.GetChatMessageContentAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(chatMessage.ModelId);
        Assert.Equal("gpt-3.5-turbo", chatMessage.ModelId);
    }

    [Fact]
    public async Task ItGetTextContentsShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(AzureChatCompletionResponse, Encoding.UTF8, "application/json") };

        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        var textContent = await chatCompletion.GetTextContentAsync("hello", this._executionSettings);

        // Assert
        Assert.NotNull(textContent.ModelId);
        Assert.Equal("gpt-3.5-turbo", textContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")));

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        await foreach (var chunk in service.GetStreamingTextContentsAsync("Prompt"))
        {
            Assert.Equal("Test chat streaming response", chunk.Text);
        }
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("model-id", "api-key", "organization", this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")));

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([]))
        {
            Assert.Equal("Test chat streaming response", chunk.Content);
        }
    }

    [Fact]
    public async Task ItAddsSystemMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(2, optionsJson.GetProperty("messages").GetArrayLength());
        Assert.Equal("Assistant is a large language model.", optionsJson.GetProperty("messages")[0].GetProperty("content").GetString());
        Assert.Equal("system", optionsJson.GetProperty("messages")[0].GetProperty("role").GetString());
        Assert.Equal("Hello", optionsJson.GetProperty("messages")[1].GetProperty("content").GetString());
        Assert.Equal("user", optionsJson.GetProperty("messages")[1].GetProperty("role").GetString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private const string ChatCompletionResponse = @"{
  ""id"": ""chatcmpl-8IlRBQU929ym1EqAY2J4T7GGkW5Om"",
  ""object"": ""chat.completion"",
  ""created"": 1699482945,
  ""model"": ""gpt-3.5-turbo"",
  ""choices"": [
    {
      ""index"": 0,
      ""message"": {
        ""role"": ""assistant"",
        ""content"": null,
        ""function_call"": {
          ""name"": ""TimePlugin_Date"",
          ""arguments"": ""{}""
        }
      },
      ""finish_reason"": ""stop""
    }
  ],
  ""usage"": {
    ""prompt_tokens"": 52,
    ""completion_tokens"": 1,
    ""total_tokens"": 53
  }
}";
    private const string AzureChatCompletionResponse = @"{
    ""id"": ""chatcmpl-8S914omCBNQ0KU1NFtxmupZpzKWv2"",
    ""object"": ""chat.completion"",
    ""created"": 1701718534,
    ""model"": ""gpt-3.5-turbo"",
    ""prompt_filter_results"": [
        {
            ""prompt_index"": 0,
            ""content_filter_results"": {
                ""hate"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""self_harm"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""sexual"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""violence"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                }
            }
        }
    ],
    ""choices"": [
        {
            ""index"": 0,
            ""finish_reason"": ""stop"",
            ""message"": {
                ""role"": ""assistant"",
                ""content"": ""Hello! How can I help you today? Please provide me with a question or topic you would like information on.""
            },
            ""content_filter_results"": {
                ""hate"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""self_harm"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""sexual"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                },
                ""violence"": {
                    ""filtered"": false,
                    ""severity"": ""safe""
                }
            }
        }
    ],
    ""usage"": {
        ""prompt_tokens"": 23,
        ""completion_tokens"": 23,
        ""total_tokens"": 46
    }
}";
}
