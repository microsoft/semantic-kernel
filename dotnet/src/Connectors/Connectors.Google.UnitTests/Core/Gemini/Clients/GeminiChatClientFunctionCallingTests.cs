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
    public async Task ChatClientWithFunctionChoiceBehaviorAutoShouldIncludeToolsInRequestAsync()
    {
        // Arrange
        var chatCompletionService = this.CreateChatCompletionService();
        var chatClient = chatCompletionService.AsChatClient();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What time is it?");

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernelWithFunctions);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.NotNull(request.Tools);
        Assert.Collection(request.Tools[0].Functions,
            item => Assert.Equal(this._timePluginDate.FullyQualifiedName, item.Name),
            item => Assert.Equal(this._timePluginNow.FullyQualifiedName, item.Name));
    }

    [Fact]
    public async Task ChatClientWithFunctionChoiceBehaviorShouldReturnFunctionCallContentAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(this._responseContentWithFunction);
        var chatCompletionService = this.CreateChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What time is it?");

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false)
        };

        // Act
        var response = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernelWithFunctions);

        // Assert
        Assert.NotNull(response);
        var geminiMessage = response as GeminiChatMessageContent;
        Assert.NotNull(geminiMessage);

        // Verify that FunctionCallContent was added to Items
        var functionCallContents = geminiMessage.Items.OfType<Microsoft.SemanticKernel.FunctionCallContent>().ToList();
        Assert.NotEmpty(functionCallContents);

        var functionCall = functionCallContents.First();
        Assert.Contains(this._timePluginNow.FunctionName, functionCall.FunctionName, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ChatClientWithAutoInvokeShouldProcessFunctionsAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var chatCompletionService = this.CreateChatCompletionService(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What time is it?");

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true)
        };

        // Act
        await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernelWithFunctions);

        // Assert
        // Verify that we made two requests (one for function call, one for final response)
        Assert.Equal(2, handlerStub.RequestContents.Count);
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
