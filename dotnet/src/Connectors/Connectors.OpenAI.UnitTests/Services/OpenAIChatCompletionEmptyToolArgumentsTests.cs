// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Tests for tool calls that come back without arguments from OpenAI compatible servers.
/// </summary>
public sealed class OpenAIChatCompletionEmptyToolArgumentsTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OpenAIChatCompletionEmptyToolArgumentsTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Theory]
    [InlineData("")]
    [InlineData("  ")]
    public async Task ItDoesNotReportAToolCallWithoutArgumentsAsInvalidJsonAsync(string arguments)
    {
        // Arrange
        string response = $$"""
            {
              "id": "response-id",
              "object": "chat.completion",
              "created": 1699896916,
              "model": "gpt-4o",
              "choices": [
                {
                  "index": 0,
                  "message": {
                    "role": "assistant",
                    "content": null,
                    "tool_calls": [
                      { "id": "1", "type": "function", "function": { "name": "MyPlugin-GetTime", "arguments": "{{arguments}}" } }
                    ]
                  },
                  "finish_reason": "tool_calls"
                }
              ],
              "usage": { "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15 }
            }
            """;
        using var httpResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(response, Encoding.UTF8, "application/json") };
        this._messageHandlerStub.ResponseToReturn = httpResponse;

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => "noon", "GetTime")]);
        var sut = new OpenAIChatCompletionService(modelId: "gpt-4o", apiKey: "NOKEY", httpClient: this._httpClient);

        // Act
        var result = await sut.GetChatMessageContentAsync(
            new ChatHistory("What time is it?"),
            new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) },
            kernel);

        // Assert
        var functionCall = Assert.Single(result.Items.OfType<FunctionCallContent>());
        Assert.Null(functionCall.Exception);
        Assert.Null(functionCall.Arguments);
        Assert.Equal("GetTime", functionCall.FunctionName);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
