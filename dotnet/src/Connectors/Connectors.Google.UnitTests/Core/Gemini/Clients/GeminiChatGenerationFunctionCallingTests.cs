// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini.Clients;

public sealed class GeminiChatGenerationFunctionCallingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly string _responseContent;
    private readonly string _responseContentWithFunction;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly GeminiFunction _timePluginDate, _timePluginNow;
    private readonly Kernel _kernelWithFunctions;
    private const string ChatTestDataFilePath = "./TestData/chat_one_response.json";
    private const string ChatTestDataWithFunctionFilePath = "./TestData/chat_one_function_response.json";

    public GeminiChatGenerationFunctionCallingTests()
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
    public async Task ShouldPassToolsToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableFunctions([this._timePluginDate, this._timePluginNow])
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.NotNull(request.Tools);
        Assert.Collection(request.Tools[0].Functions,
            item => Assert.Equal(this._timePluginDate.FullyQualifiedName, item.Name),
            item => Assert.Equal(this._timePluginNow.FullyQualifiedName, item.Name));
        Assert.Collection(request.Tools[0].Functions,
            item =>
                Assert.Equal(JsonSerializer.Serialize(this._timePluginDate.ToFunctionDeclaration().Parameters),
                    JsonSerializer.Serialize(item.Parameters)),
            item =>
                Assert.Equal(JsonSerializer.Serialize(this._timePluginNow.ToFunctionDeclaration().Parameters),
                    JsonSerializer.Serialize(item.Parameters)));
    }

    [Fact]
    public async Task ShouldPassFunctionCallToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var functionCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = this._timePluginNow.FullyQualifiedName,
            Arguments = JsonSerializer.SerializeToNode(new { param1 = "hello" })
        };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, string.Empty, "modelId", [functionCallPart]));
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableFunctions([this._timePluginDate, this._timePluginNow])
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        GeminiRequest request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent)!;
        var content = request.Contents.LastOrDefault();
        Assert.NotNull(content);
        Assert.Equal(AuthorRole.Assistant, content.Role);
        var functionCall = content.Parts![0].FunctionCall;
        Assert.NotNull(functionCall);
        Assert.Equal(functionCallPart.FunctionName, functionCall.FunctionName);
        Assert.Equal(JsonSerializer.Serialize(functionCallPart.Arguments), functionCall.Arguments!.ToJsonString());
    }

    [Fact]
    public async Task ShouldPassFunctionResponseToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var functionCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = this._timePluginNow.FullyQualifiedName,
            Arguments = JsonSerializer.SerializeToNode(new { param1 = "hello" })
        };
        var toolCall = new GeminiFunctionToolCall(functionCallPart);
        this._kernelWithFunctions.Plugins["TimePlugin"].TryGetFunction("Now", out var timeNowFunction);
        var toolCallResponse = new GeminiFunctionToolResult(
            toolCall,
            new FunctionResult(timeNowFunction!, new { time = "Time now" }));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, string.Empty, "modelId", [functionCallPart]));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Tool, string.Empty, "modelId", toolCallResponse));
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableFunctions([this._timePluginDate, this._timePluginNow])
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        GeminiRequest request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent)!;
        var content = request.Contents.LastOrDefault();
        Assert.NotNull(content);
        Assert.Equal(AuthorRole.Tool, content.Role);
        var functionResponse = content.Parts![0].FunctionResponse;
        Assert.NotNull(functionResponse);
        Assert.Equal(toolCallResponse.FullyQualifiedName, functionResponse.FunctionName);
        Assert.Equal(JsonSerializer.Serialize(toolCallResponse.FunctionResult.GetValue<object>()), functionResponse.Response.Arguments.ToJsonString());
    }

    [Fact]
    public async Task ShouldReturnFunctionsCalledByModelAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(this._responseContentWithFunction);
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableFunctions([this._timePluginDate, this._timePluginNow])
        };

        // Act
        var chatMessageContents =
            await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var message = chatMessageContents.SingleOrDefault() as GeminiChatMessageContent;
        Assert.NotNull(message);
        Assert.NotNull(message.ToolCalls);
        Assert.Single(message.ToolCalls,
            item => item.FullyQualifiedName == this._timePluginNow.FullyQualifiedName);
        Assert.Single(message.ToolCalls,
            item => item.Arguments!["param1"]!.ToString()!.Equals("hello", StringComparison.Ordinal));
    }

    [Fact]
    public async Task IfAutoInvokeShouldAddFunctionsCalledByModelToChatHistoryAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var messages = chatHistory.OfType<GeminiChatMessageContent>();
        var contents = messages.Where(item =>
            item.Role == AuthorRole.Assistant &&
            item.ToolCalls is not null &&
            item.ToolCalls.Any(toolCall => toolCall.FullyQualifiedName == this._timePluginNow.FullyQualifiedName) &&
            item.ToolCalls.Any(toolCall => toolCall.Arguments!["param1"]!.ToString()!.Equals("hello", StringComparison.Ordinal)));
        Assert.Single(contents);
    }

    [Fact]
    public async Task IfAutoInvokeShouldAddFunctionResponseToChatHistoryAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var messages = chatHistory.OfType<GeminiChatMessageContent>();
        var contents = messages.Where(item =>
            item.Role == AuthorRole.Tool &&
            item.CalledToolResult is not null &&
            item.CalledToolResult.FullyQualifiedName == this._timePluginNow.FullyQualifiedName &&
            DateTime.TryParse(item.CalledToolResult.FunctionResult.ToString(), provider: new DateTimeFormatInfo(), DateTimeStyles.AssumeLocal, out _));
        Assert.Single(contents);
    }

    [Fact]
    public async Task IfAutoInvokeShouldReturnAssistantMessageWithContentAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        var messages =
            await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        Assert.Single(messages, item =>
            item.Role == AuthorRole.Assistant && !string.IsNullOrWhiteSpace(item.Content));
    }

    [Fact]
    public async Task IfAutoInvokeShouldPassToolsToEachRequestAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };
        // used reflection to simplify the test
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumUseAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 100);
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumAutoInvokeAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 10);

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var requests = handlerStub.RequestContents
            .Select(bytes => JsonSerializer.Deserialize<GeminiRequest>(bytes)).ToList();
        Assert.Collection(requests,
            item => Assert.NotNull(item!.Tools),
            item => Assert.NotNull(item!.Tools));
        Assert.Collection(requests,
            item => Assert.Collection(item!.Tools![0].Functions,
                func => Assert.Equal(this._timePluginDate.FullyQualifiedName, func.Name),
                func => Assert.Equal(this._timePluginNow.FullyQualifiedName, func.Name)),
            item => Assert.Collection(item!.Tools![0].Functions,
                func => Assert.Equal(this._timePluginDate.FullyQualifiedName, func.Name),
                func => Assert.Equal(this._timePluginNow.FullyQualifiedName, func.Name)));
    }

    [Fact]
    public async Task IfAutoInvokeMaximumUseAttemptsReachedShouldNotPassToolsToSubsequentRequestsAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };
        // used reflection to simplify the test
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumUseAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 1);
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumAutoInvokeAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 1);

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var requests = handlerStub.RequestContents
            .Select(bytes => JsonSerializer.Deserialize<GeminiRequest>(bytes)).ToList();
        Assert.Collection(requests,
            item => Assert.NotNull(item!.Tools),
            item => Assert.Null(item!.Tools));
    }

    [Fact]
    public async Task IfAutoInvokeMaximumAutoInvokeAttemptsReachedShouldStopInvokingAndReturnToolCallsAsync()
    {
        // Arrange
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };
        // used reflection to simplify the test
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumUseAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 100);
        typeof(GeminiToolCallBehavior)
            .GetField($"<{nameof(GeminiToolCallBehavior.MaximumAutoInvokeAttempts)}>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!
            .SetValue(executionSettings.ToolCallBehavior, 1);

        // Act
        var messages =
            await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        var geminiMessage = messages[0] as GeminiChatMessageContent;
        Assert.NotNull(geminiMessage);
        Assert.NotNull(geminiMessage.ToolCalls);
        Assert.NotEmpty(geminiMessage.ToolCalls);

        // Chat history should contain the tool call from first invocation
        Assert.Contains(chatHistory, c =>
            c is GeminiChatMessageContent gm && gm.Role == AuthorRole.Tool && gm.CalledToolResult is not null);
    }

    [Fact]
    public async Task ShouldBatchMultipleToolResponsesIntoSingleMessageAsync()
    {
        // Arrange
        var responseContentWithMultipleFunctions = File.ReadAllText("./TestData/chat_multiple_function_calls_response.json")
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);

        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(responseContentWithMultipleFunctions);
        handlerStub.AddJsonResponse(this._responseContent); // Final response after tool execution

#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        // Find the tool response message that should be batched
        var toolResponseMessage = chatHistory.OfType<GeminiChatMessageContent>()
            .FirstOrDefault(m => m.Role == AuthorRole.Tool && m.CalledToolResults != null);

        Assert.NotNull(toolResponseMessage);
        Assert.NotNull(toolResponseMessage.CalledToolResults);

        // Verify that multiple tool results are batched into a single message
        Assert.Equal(2, toolResponseMessage.CalledToolResults.Count);

        // Verify the specific tool calls that were batched
        var toolNames = toolResponseMessage.CalledToolResults.Select(tr => tr.FullyQualifiedName).ToArray();
        Assert.Contains(this._timePluginNow.FullyQualifiedName, toolNames);
        Assert.Contains(this._timePluginDate.FullyQualifiedName, toolNames);

        // Verify backward compatibility - CalledToolResult property should return the first result
        Assert.NotNull(toolResponseMessage.CalledToolResult);
        Assert.Equal(toolResponseMessage.CalledToolResults[0], toolResponseMessage.CalledToolResult);

        // Verify the request that would be sent to Gemini contains the correct structure
        var requestJson = handlerStub.GetRequestContentAsString(1); // Get the second request (after tool execution)
        Assert.NotNull(requestJson);
        var request = JsonSerializer.Deserialize<GeminiRequest>(requestJson);
        Assert.NotNull(request);

        // Find the content that represents the batched tool responses
        var toolResponseContent = request.Contents.FirstOrDefault(c => c.Role == AuthorRole.Tool);
        Assert.NotNull(toolResponseContent);
        Assert.NotNull(toolResponseContent.Parts);

        // Verify that all function responses are included as separate parts in the single message
        var functionResponseParts = toolResponseContent.Parts.Where(p => p.FunctionResponse != null).ToArray();
        Assert.Equal(2, functionResponseParts.Length);

        // Verify each function response part corresponds to the tool calls
        var functionNames = functionResponseParts.Select(p => p.FunctionResponse!.FunctionName).ToArray();
        Assert.Contains(this._timePluginNow.FullyQualifiedName, functionNames);
        Assert.Contains(this._timePluginDate.FullyQualifiedName, functionNames);
    }

    [Fact]
    public async Task IfAutoInvokeShouldInvokeAutoFunctionInvocationFilterAsync()
    {
        // Arrange
        int filterInvocationCount = 0;
        var autoFunctionInvocationFilter = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            filterInvocationCount++;
            await next(context);
        });

        var kernel = new Kernel();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string? format = null)
                => DateTime.Now.Date.ToString(format, CultureInfo.InvariantCulture), "Date", "TimePlugin.Date"),

            KernelFunctionFactory.CreateFromMethod(()
                    => DateTime.Now.ToString("", CultureInfo.InvariantCulture), "Now", "TimePlugin.Now",
                parameters: [new KernelParameterMetadata("param1") { ParameterType = typeof(string), Description = "desc", IsRequired = false }]),
        }));
        kernel.AutoFunctionInvocationFilters.Add(autoFunctionInvocationFilter);

        // Use multiple function calls response to that filter is invoked for each tool call
        var responseContentWithMultipleFunctions = File.ReadAllText("./TestData/chat_multiple_function_calls_response.json")
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);

        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(responseContentWithMultipleFunctions);
        handlerStub.AddJsonResponse(this._responseContent);

#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: kernel);

        // Assert
        Assert.Equal(2, filterInvocationCount);
    }

    [Fact]
    public async Task IfAutoInvokeShouldProvideCorrectContextToAutoFunctionInvocationFilterAsync()
    {
        // Arrange
        AutoFunctionInvocationContext? capturedContext = null;
        var autoFunctionInvocationFilter = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            capturedContext = context;
            await next(context);
        });

        var kernel = new Kernel();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod(()
                    => DateTime.Now.ToString("", CultureInfo.InvariantCulture), "Now", "TimePlugin.Now"),
        }));
        kernel.AutoFunctionInvocationFilters.Add(autoFunctionInvocationFilter);

        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);

#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: kernel);

        // Assert
        Assert.NotNull(capturedContext);
        Assert.Equal(0, capturedContext.RequestSequenceIndex); // First request
        Assert.Equal(0, capturedContext.FunctionSequenceIndex); // First function in the batch
        Assert.Equal(1, capturedContext.FunctionCount); // One function call in this response
        Assert.NotNull(capturedContext.Function);
        Assert.Equal("Now", capturedContext.Function.Name);
        Assert.NotNull(capturedContext.ChatHistory);
        Assert.NotNull(capturedContext.Result);
    }

    [Fact]
    public async Task IfAutoInvokeShouldTerminateWhenFilterRequestsTerminationAsync()
    {
        // Arrange
        int filterInvocationCount = 0;
        var autoFunctionInvocationFilter = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            filterInvocationCount++;
            context.Terminate = true;
            await next(context);
        });

        var kernel = new Kernel();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string param1)
                    => DateTime.Now.ToString("", CultureInfo.InvariantCulture), "Now", "TimePlugin.Now"),

            KernelFunctionFactory.CreateFromMethod((string format)
                    => DateTime.Now.ToString("", CultureInfo.InvariantCulture), "Date", "TimePlugin.Date"),
        }));
        kernel.AutoFunctionInvocationFilters.Add(autoFunctionInvocationFilter);

        // Use multiple function calls response to verify termination stops processing additional tool calls
        var responseContentWithMultipleFunctions = File.ReadAllText("./TestData/chat_multiple_function_calls_response.json")
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);

        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(responseContentWithMultipleFunctions);
        handlerStub.AddJsonResponse(this._responseContent); // This should not be called due to termination

#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        var result = await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: kernel);

        // Assert
        // Filter should have been invoked only once (for the first tool call) because termination was requested
        Assert.Equal(1, filterInvocationCount);
        // Only 1 request should be made since termination happens after receiving the tool calls
        // but before making the second request to the model with the tool results
        Assert.Single(handlerStub.RequestContents);
    }

    [Fact]
    public async Task IfAutoInvokeShouldAllowFilterToModifyFunctionResultAsync()
    {
        // Arrange
        const string ModifiedResult = "Modified result by filter";
        var autoFunctionInvocationFilter = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            await next(context);
            // Modify the result after function execution
            context.Result = new FunctionResult(context.Function, ModifiedResult);
        });

        var kernel = new Kernel();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod(()
                    => "Original result", "Now", "TimePlugin.Now"),
        }));
        kernel.AutoFunctionInvocationFilters.Add(autoFunctionInvocationFilter);

        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(this._responseContentWithFunction);
        handlerStub.AddJsonResponse(this._responseContent);

#pragma warning disable CA2000
        var client = this.CreateChatCompletionClient(httpClient: handlerStub.CreateHttpClient());
#pragma warning restore CA2000
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: kernel);

        // Assert - Check that the modified result was sent to the model
        var secondRequestContent = handlerStub.GetRequestContentAsString(1);
        Assert.NotNull(secondRequestContent);
        Assert.Contains(ModifiedResult, secondRequestContent);
    }

    [Fact]
    public async Task FunctionCallWithThoughtSignatureIsCapturedInToolCallAsync()
    {
        // Arrange
        var responseWithThoughtSignature = File.ReadAllText("./TestData/chat_function_with_thought_signature_response.json")
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(responseWithThoughtSignature);

        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableFunctions([this._timePluginNow])
        };

        // Act
        var messages = await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert
        Assert.Single(messages);
        var geminiMessage = messages[0] as GeminiChatMessageContent;
        Assert.NotNull(geminiMessage);
        Assert.NotNull(geminiMessage.ToolCalls);
        Assert.Single(geminiMessage.ToolCalls);
        Assert.Equal("test-thought-signature-abc123", geminiMessage.ToolCalls[0].ThoughtSignature);
    }

    [Fact]
    public async Task TextResponseWithThoughtSignatureIsCapturedInMetadataAsync()
    {
        // Arrange
        var responseWithThoughtSignature = File.ReadAllText("./TestData/chat_text_with_thought_signature_response.json");
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(responseWithThoughtSignature);

        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var messages = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.Single(messages);
        var geminiMessage = messages[0] as GeminiChatMessageContent;
        Assert.NotNull(geminiMessage);
        Assert.NotNull(geminiMessage.Metadata);
        var metadata = geminiMessage.Metadata as GeminiMetadata;
        Assert.NotNull(metadata);
        Assert.Equal("text-response-thought-signature-xyz789", metadata.ThoughtSignature);
    }

    [Fact]
    public async Task ThoughtSignatureIsIncludedInSubsequentRequestAsync()
    {
        // Arrange - First response has function call with ThoughtSignature
        var responseWithThoughtSignature = File.ReadAllText("./TestData/chat_function_with_thought_signature_response.json")
            .Replace("%nameSeparator%", GeminiFunction.NameSeparator, StringComparison.Ordinal);
        using var handlerStub = new MultipleHttpMessageHandlerStub();
        handlerStub.AddJsonResponse(responseWithThoughtSignature);
        handlerStub.AddJsonResponse(this._responseContent); // Second response is text

        using var httpClient = new HttpClient(handlerStub, false);
        var client = this.CreateChatCompletionClient(httpClient: httpClient);
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings, kernel: this._kernelWithFunctions);

        // Assert - Check that the second request includes the ThoughtSignature
        var secondRequestContent = handlerStub.GetRequestContentAsString(1);
        Assert.NotNull(secondRequestContent);
        Assert.Contains("test-thought-signature-abc123", secondRequestContent);
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    private GeminiChatCompletionClient CreateChatCompletionClient(
        string modelId = "fake-model",
        HttpClient? httpClient = null)
    {
        return new GeminiChatCompletionClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            apiVersion: GoogleAIVersion.V1,
            apiKey: "fake-key");
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private sealed class AutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> _callback;

        public AutoFunctionInvocationFilter(Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> callback)
        {
            this._callback = callback;
        }

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await this._callback(context, next);
        }
    }
}
