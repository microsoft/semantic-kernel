// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletion;

/// <summary>
/// Unit tests for <see cref="OpenAIChatCompletion"/>
/// </summary>
public sealed class OpenAIChatCompletionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly OpenAIRequestSettings _requestSettings;

    public OpenAIChatCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._requestSettings = new()
        {
            Functions = new List<OpenAIFunction>()
            {
                new OpenAIFunction
                {
                    FunctionName = "Date",
                    PluginName = "TimePlugin",
                    Description = "TimePlugin.Date",
                    Parameters = new List<OpenAIFunctionParameter>()
                    {
                        new OpenAIFunctionParameter
                        {
                            Name = "Format",
                            Description = "Date format",
                            Type = "string",
                            IsRequired = false,
                        }
                    }
                },
                new OpenAIFunction
                {
                    FunctionName = "Now",
                    PluginName = "TimePlugin",
                    Description = "TimePlugin.Now",
                    Parameters = new List<OpenAIFunctionParameter>()
                    {
                        new OpenAIFunctionParameter
                        {
                            Name = "Format",
                            Description = "Date format",
                            Type = "string",
                            IsRequired = false,
                        }
                    }
                }
            }
        };
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionsWhenUsingAutoAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletion(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._requestSettings.FunctionCall = "auto";

        // Act
        await chatCompletion.GetChatCompletionsAsync(new ChatHistory(), this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(2, optionsJson.GetProperty("functions").GetArrayLength());
        Assert.Equal("TimePlugin-Date", optionsJson.GetProperty("functions")[0].GetProperty("name").GetString());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("functions")[1].GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionsWhenUsingNowAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletion(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._requestSettings.FunctionCall = "TimePlugin-Now";

        // Act
        await chatCompletion.GetChatCompletionsAsync(new ChatHistory(), this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("functions").GetArrayLength());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("functions")[0].GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesNoFunctionsWhenUsingNoneAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletion(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._requestSettings.FunctionCall = "none";

        // Act
        await chatCompletion.GetChatCompletionsAsync(new ChatHistory(), this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.False(optionsJson.TryGetProperty("functions", out var _));
    }

    [Fact]
    public async Task ItAddsNameToChatMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletion(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello", new Dictionary<string, string>() { { "Name", "John Doe" } });

        // Act
        await chatCompletion.GetChatCompletionsAsync(chatHistory, this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("messages").GetArrayLength());
        Assert.Equal("John Doe", optionsJson.GetProperty("messages")[0].GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItAddsNameAndArgumentsToChatMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletion(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello", new Dictionary<string, string>() { { "Name", "SayHello" }, { "Arguments", "{ \"user\": \"John Doe\" }" } });

        // Act
        await chatCompletion.GetChatCompletionsAsync(chatHistory, this._requestSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("messages").GetArrayLength());
        Assert.Equal("SayHello", optionsJson.GetProperty("messages")[0].GetProperty("name").GetString());
        Assert.Equal("SayHello", optionsJson.GetProperty("messages")[0].GetProperty("function_call").GetProperty("name").GetString());
        Assert.Equal("{ \"user\": \"John Doe\" }", optionsJson.GetProperty("messages")[0].GetProperty("function_call").GetProperty("arguments").GetString());
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
          ""name"": ""TimePlugin-Date"",
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
}
