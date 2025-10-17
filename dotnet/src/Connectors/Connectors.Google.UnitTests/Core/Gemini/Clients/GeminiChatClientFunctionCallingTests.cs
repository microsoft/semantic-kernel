// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini.Clients;

/// <summary>
/// Unit tests for IChatClient-based function calling with Gemini using FunctionChoiceBehavior.
/// </summary>
public sealed class GeminiChatClientFunctionCallingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly string _responseContent;
    private readonly string _responseContentWithFunction;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly GeminiFunction _timePluginDate, _timePluginNow;
    private readonly Kernel _kernelWithFunctions;
    private const string ChatTestDataFilePath = "./TestData/chat_one_response.json";
    private const string ChatTestDataWithFunctionFilePath = "./TestData/chat_one_function_response.json";

    public GeminiChatClientFunctionCallingTests()
    {
        this._responseContent = File.ReadAllText(ChatTestDataFilePath);
        this._responseContentWithFunction = File.ReadAllText(ChatTestDataWithFunctionFilePath)
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            this._responseContent);

        this._httpClient = new HttpClient(this._messageHandlerStub, false);

        var kernelPlugin = KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string? format = null)
                => DateTime.Now.Date.ToString(format, CultureInfo.InvariantCulture), "Date", "TimePlugin.Date"),
            KernelFunctionFactory.CreateFromMethod(()
                    => DateTime.Now.ToString("", CultureInfo.InvariantCulture), "Now", "TimePlugin.Now",
                parameters: [new KernelParameterMetadata("param1") { ParameterType = typeof(string), Description = "desc", IsRequired = false }]),
        });
        IList<KernelFunctionMetadata> functions = kernelPlugin.GetFunctionsMetadata();

        this._timePluginDate = functions[0].ToGeminiFunction();
        this._timePluginNow = functions[1].ToGeminiFunction();

        this._kernelWithFunctions = new Kernel();
        this._kernelWithFunctions.Plugins.Add(kernelPlugin);
    }

    [Fact]
    public async Task ChatClientShouldConvertToIChatClientSuccessfullyAsync()
    {
        // Arrange
        var chatCompletionService = this.CreateChatCompletionService();

        // Act
        var chatClient = chatCompletionService.AsChatClient();

        // Assert - Verify conversion works
        Assert.NotNull(chatClient);
        Assert.IsAssignableFrom<IChatClient>(chatClient);

        // Verify we can make a basic call through IChatClient
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What time is it?")
        };

        var response = await chatClient.GetResponseAsync(messages);

        Assert.NotNull(response);
        Assert.NotEmpty(response.Messages);
    }

    [Fact]
    public async Task ChatClientShouldReceiveFunctionCallsInResponseAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(this._responseContentWithFunction);
        var chatCompletionService = this.CreateChatCompletionService();
        var chatClient = chatCompletionService.AsChatClient();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false)
        };
        var chatOptions = settings.ToChatOptions(this._kernelWithFunctions);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What time is it?")
        };

        // Act
        var response = await chatClient.GetResponseAsync(messages, chatOptions);

        // Assert - Verify that FunctionCallContent is returned in the response
        Assert.NotNull(response);
        var functionCalls = response.Messages
            .SelectMany(m => m.Contents)
            .OfType<Microsoft.Extensions.AI.FunctionCallContent>()
            .ToList();

        Assert.NotEmpty(functionCalls);
        var functionCall = functionCalls.First();
        Assert.Contains(this._timePluginNow.FunctionName, functionCall.Name, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ChatClientShouldStreamResponsesAsync()
    {
        // Arrange
        var chatCompletionService = this.CreateChatCompletionService();
        var chatClient = chatCompletionService.AsChatClient();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };
        var chatOptions = settings.ToChatOptions(this._kernelWithFunctions);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "What time is it?")
        };

        // Act
        var updates = new List<ChatResponseUpdate>();
        await foreach (var update in chatClient.GetStreamingResponseAsync(messages, chatOptions))
        {
            updates.Add(update);
        }

        // Assert - Verify that streaming works and returns updates
        Assert.NotEmpty(updates);
    }

    [Fact]
    public async Task AsChatClientConvertsServiceToIChatClientAsync()
    {
        // Arrange
        var chatCompletionService = this.CreateChatCompletionService();

        // Act
        var chatClient = chatCompletionService.AsChatClient();

        // Assert
        Assert.NotNull(chatClient);
        Assert.IsAssignableFrom<IChatClient>(chatClient);
    }

    private GoogleAIGeminiChatCompletionService CreateChatCompletionService(HttpClient? httpClient = null)
    {
        return new GoogleAIGeminiChatCompletionService(
            modelId: "fake-model",
            apiKey: "fake-key",
            apiVersion: GoogleAIVersion.V1,
            httpClient: httpClient ?? this._httpClient);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
