// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Represents a client for interacting with the chat completion Gemini model.
/// </summary>
internal sealed class GeminiChatCompletionClient : ClientBase
{
    private const string ModelProvider = "google";
    private readonly StreamJsonParser _streamJsonParser = new();
    private readonly string _modelId;
    private readonly Uri _chatGenerationEndpoint;
    private readonly Uri _chatStreamingEndpoint;

    private static readonly string s_namespace = typeof(GoogleAIGeminiChatCompletionService).Namespace!;

    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertise itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 128;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new(s_namespace);

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    private static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    private static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    private static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: $"{s_namespace}.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    /// <summary>
    /// Represents a client for interacting with the chat completion Gemini model via GoogleAI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="apiKey">Api key for GoogleAI endpoint</param>
    /// <param name="apiVersion">Version of the Google API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            logger: logger,
            apiKey: apiKey)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._chatGenerationEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._modelId}:generateContent");
        this._chatStreamingEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._modelId}:streamGenerateContent?alt=sse");
    }

    /// <summary>
    /// Represents a client for interacting with the chat completion Gemini model via VertexAI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="bearerTokenProvider">Bearer key provider used for authentication</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Project ID from google cloud</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            logger: logger,
            bearerTokenProvider: bearerTokenProvider)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(location);
        Verify.ValidHostnameSegment(location);
        Verify.NotNullOrWhiteSpace(projectId);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._chatGenerationEndpoint = new Uri($"https://{location}-aiplatform.googleapis.com/{versionSubLink}/projects/{projectId}/locations/{location}/publishers/google/models/{this._modelId}:generateContent");
        this._chatStreamingEndpoint = new Uri($"https://{location}-aiplatform.googleapis.com/{versionSubLink}/projects/{projectId}/locations/{location}/publishers/google/models/{this._modelId}:streamGenerateContent?alt=sse");
    }

    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var state = this.ValidateInputAndCreateChatCompletionState(chatHistory, kernel, executionSettings);

        for (state.Iteration = 1; ; state.Iteration++)
        {
            List<GeminiChatMessageContent> chatResponses;
            using (var activity = ModelDiagnostics.StartCompletionActivity(
                this._chatGenerationEndpoint, this._modelId, ModelProvider, chatHistory, state.ExecutionSettings))
            {
                GeminiResponse geminiResponse;
                try
                {
                    geminiResponse = await this.SendRequestAndReturnValidGeminiResponseAsync(
                            this._chatGenerationEndpoint, state.GeminiRequest, cancellationToken)
                        .ConfigureAwait(false);
                    chatResponses = this.ProcessChatResponse(geminiResponse);
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    throw;
                }

                activity?.SetCompletionResponse(
                    chatResponses,
                    geminiResponse.UsageMetadata?.PromptTokenCount,
                    geminiResponse.UsageMetadata?.CandidatesTokenCount);
            }

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!state.AutoInvoke || chatResponses.Count != 1)
            {
                return chatResponses;
            }

            state.LastMessage = chatResponses[0];
            if (state.LastMessage.ToolCalls is null || state.LastMessage.ToolCalls.Count == 0)
            {
                return chatResponses;
            }

            // ToolCallBehavior is not null because we are in auto-invoke mode but we check it again to be sure it wasn't changed in the meantime
            Verify.NotNull(state.ExecutionSettings.ToolCallBehavior);

            state.AddLastMessageToChatHistoryAndRequest();
            await this.ProcessFunctionsAsync(state, cancellationToken).ConfigureAwait(false);

            // Check if filter explicitly requested termination
            // and return the last chat message content that was added to chat history
            if (state.FilterTerminationRequested)
            {
                return [state.ChatHistory.Last()];
            }
        }
    }

    /// <summary>
    /// Generates a stream of chat messages asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingChatMessageContent"/> streaming chat contents.</returns>
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var state = this.ValidateInputAndCreateChatCompletionState(chatHistory, kernel, executionSettings);

        for (state.Iteration = 1; ; state.Iteration++)
        {
            using (var activity = ModelDiagnostics.StartCompletionActivity(
                this._chatGenerationEndpoint, this._modelId, ModelProvider, chatHistory, state.ExecutionSettings))
            {
                HttpResponseMessage? httpResponseMessage = null;
                Stream? responseStream = null;
                try
                {
                    using var httpRequestMessage = await this.CreateHttpRequestAsync(state.GeminiRequest, this._chatStreamingEndpoint).ConfigureAwait(false);
                    httpResponseMessage = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
                    responseStream = await httpResponseMessage.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    activity?.SetError(ex);
                    httpResponseMessage?.Dispose();
                    responseStream?.Dispose();
                    throw;
                }

                var responseEnumerator = this.GetStreamingChatMessageContentsOrPopulateStateForToolCallingAsync(state, responseStream, cancellationToken)
                    .GetAsyncEnumerator(cancellationToken);
                List<StreamingChatMessageContent>? streamedContents = activity is not null ? [] : null;
                try
                {
                    while (true)
                    {
                        try
                        {
                            if (!await responseEnumerator.MoveNextAsync().ConfigureAwait(false))
                            {
                                break;
                            }
                        }
                        catch (Exception ex) when (activity is not null)
                        {
                            activity.SetError(ex);
                            throw;
                        }

                        streamedContents?.Add(responseEnumerator.Current);
                        yield return responseEnumerator.Current;
                    }
                }
                finally
                {
                    activity?.EndStreaming(streamedContents);
                    httpResponseMessage?.Dispose();
                    responseStream?.Dispose();
                    await responseEnumerator.DisposeAsync().ConfigureAwait(false);
                }
            }

            if (!state.AutoInvoke)
            {
                yield break;
            }

            // ToolCallBehavior is not null because we are in auto-invoke mode but we check it again to be sure it wasn't changed in the meantime
            Verify.NotNull(state.ExecutionSettings.ToolCallBehavior);

            state.AddLastMessageToChatHistoryAndRequest();
            await this.ProcessFunctionsAsync(state, cancellationToken).ConfigureAwait(false);

            // Check if filter explicitly requested termination
            // and yield the last chat message content that was added to chat history
            if (state.FilterTerminationRequested)
            {
                var lastMessage = state.ChatHistory.Last();
                yield return new StreamingChatMessageContent(lastMessage.Role, lastMessage.Content);
                yield break;
            }
        }
    }

    private ChatCompletionState ValidateInputAndCreateChatCompletionState(
        ChatHistory chatHistory,
        Kernel? kernel,
        PromptExecutionSettings? executionSettings)
    {
        ValidateChatHistory(chatHistory);

        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            // JsonSerializer can't serialize Type. Get schema JsonElement
            if (geminiExecutionSettings.ResponseSchema is Type)
            {
                geminiExecutionSettings.ResponseSchema = GeminiRequest.GetResponseSchemaConfig(geminiExecutionSettings.ResponseSchema);
            }

            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(geminiExecutionSettings));
        }

        return new ChatCompletionState()
        {
            AutoInvoke = CheckAutoInvokeCondition(kernel, geminiExecutionSettings),
            ChatHistory = chatHistory,
            ExecutionSettings = geminiExecutionSettings,
            GeminiRequest = CreateRequest(chatHistory, geminiExecutionSettings, kernel),
            Kernel = kernel! // not null if auto-invoke is true
        };
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsOrPopulateStateForToolCallingAsync(
        ChatCompletionState state,
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken ct)
    {
        var chatResponsesEnumerable = this.ProcessChatResponseStreamAsync(responseStream, ct: ct);
        IAsyncEnumerator<GeminiChatMessageContent> chatResponsesEnumerator = null!;
        try
        {
            chatResponsesEnumerator = chatResponsesEnumerable.GetAsyncEnumerator(ct);
            while (await chatResponsesEnumerator.MoveNextAsync().ConfigureAwait(false))
            {
                var messageContent = chatResponsesEnumerator.Current;
                if (state.AutoInvoke && messageContent.ToolCalls is { Count: > 0 })
                {
                    if (await chatResponsesEnumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        // We disable auto-invoke because we have more than one message in the stream.
                        // This scenario should not happen but I leave it as a precaution
                        state.AutoInvoke = false;
                        // We return the first message
                        yield return this.GetStreamingChatContentFromChatContent(messageContent);
                        // We return the second message
                        messageContent = chatResponsesEnumerator.Current;
                        yield return this.GetStreamingChatContentFromChatContent(messageContent);
                        continue;
                    }

                    // If function call was returned there is no more data in stream
                    state.LastMessage = messageContent;

                    // Yield the message also if it contains text
                    if (!string.IsNullOrWhiteSpace(messageContent.Content))
                    {
                        yield return this.GetStreamingChatContentFromChatContent(messageContent);
                    }

                    yield break;
                }

                // If we don't want to attempt to invoke any functions, just return the result.
                yield return this.GetStreamingChatContentFromChatContent(messageContent);
            }
        }
        finally
        {
            if (chatResponsesEnumerator is not null)
            {
                await chatResponsesEnumerator.DisposeAsync().ConfigureAwait(false);
            }
        }
    }

    private async Task ProcessFunctionsAsync(ChatCompletionState state, CancellationToken cancellationToken)
    {
        if (this.Logger.IsEnabled(LogLevel.Debug))
        {
            this.Logger.LogDebug("Tool requests: {Requests}", state.LastMessage!.ToolCalls!.Count);
        }

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("Function call requests: {FunctionCall}",
                string.Join(", ", state.LastMessage!.ToolCalls!.Select(ftc => ftc.ToString())));
        }

        // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
        // Collect all tool responses before adding to chat history
        var toolResponses = new List<GeminiChatMessageContent>();

        int toolCallIndex = 0;
        foreach (var toolCall in state.LastMessage!.ToolCalls!)
        {
            var (toolResponse, terminationRequested) = await this.ProcessSingleToolCallWithFiltersAsync(
                state, toolCall, toolCallIndex, cancellationToken).ConfigureAwait(false);
            toolResponses.Add(toolResponse);

            // If filter requested termination, stop processing more tool calls
            if (terminationRequested)
            {
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Filter requested termination of automatic function invocation.");
                }
                state.AutoInvoke = false;
                state.FilterTerminationRequested = true;
                break;
            }

            toolCallIndex++;
        }

        // Add all tool responses as a single batched message
        this.AddBatchedToolResponseMessage(state.ChatHistory, state.GeminiRequest, toolResponses);

        // Clear the tools. If we end up wanting to use tools, we'll reset it to the desired value.
        state.GeminiRequest.Tools = null;

        if (state.Iteration >= state.ExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
        {
            // Don't add any tools as we've reached the maximum attempts limit.
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tools.",
                    state.ExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
            }
        }
        else
        {
            // Regenerate the tool list as necessary. The invocation of the function(s) could have augmented
            // what functions are available in the kernel.
            state.ExecutionSettings.ToolCallBehavior!.ConfigureGeminiRequest(state.Kernel, state.GeminiRequest);
        }

        // Disable auto invocation if we've exceeded the allowed limit.
        if (state.Iteration >= state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
        {
            state.AutoInvoke = false;
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.",
                    state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
            }
        }
    }

    private async Task<(GeminiChatMessageContent, bool terminationRequested)> ProcessSingleToolCallWithFiltersAsync(
        ChatCompletionState state,
        GeminiFunctionToolCall toolCall,
        int toolCallIndex,
        CancellationToken cancellationToken)
    {
        // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
        // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
        // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
        if (state.ExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
            !IsRequestableTool(state.GeminiRequest.Tools![0].Functions, toolCall))
        {
            return (this.CreateToolResponseMessage(toolCall, functionResponse: null, "Error: Function call request for a function that wasn't defined."), false);
        }

        // Ensure the provided function exists for calling
        if (!state.Kernel!.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? functionArgs))
        {
            return (this.CreateToolResponseMessage(toolCall, functionResponse: null, "Error: Requested function could not be found."), false);
        }

        // Create the invocation context for the filter pipeline
        FunctionResult functionResult = new(function) { Culture = state.Kernel.Culture };
        AutoFunctionInvocationContext invocationContext = new(
            state.Kernel,
            function,
            functionResult,
            state.ChatHistory,
            state.LastMessage!)
        {
            Arguments = functionArgs,
            RequestSequenceIndex = state.Iteration - 1,
            FunctionSequenceIndex = toolCallIndex,
            FunctionCount = state.LastMessage!.ToolCalls!.Count,
            CancellationToken = cancellationToken
        };

        // Now, invoke the function through the filter pipeline
        s_inflightAutoInvokes.Value++;
        try
        {
            invocationContext = await OnAutoFunctionInvocationAsync(
                state.Kernel,
                invocationContext,
                async (context) =>
                {
                    // Check if filter requested termination.
                    if (context.Terminate)
                    {
                        return;
                    }

                    // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                    // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                    // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                    context.Result = await function.InvokeAsync(state.Kernel, invocationContext.Arguments, cancellationToken: cancellationToken)
                        .ConfigureAwait(false);
                }).ConfigureAwait(false);
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch (Exception e)
#pragma warning restore CA1031
        {
            return (this.CreateToolResponseMessage(toolCall, functionResponse: null, $"Error: Exception while invoking function. {e.Message}"), false);
        }
        finally
        {
            s_inflightAutoInvokes.Value--;
        }

        // Apply any changes from the auto function invocation filters context to final result.
        functionResult = invocationContext.Result;

        return (this.CreateToolResponseMessage(toolCall, functionResponse: functionResult, errorMessage: null), invocationContext.Terminate);
    }

    /// <summary>
    /// Executes auto function invocation filters and/or function itself.
    /// </summary>
    private static async Task<AutoFunctionInvocationContext> OnAutoFunctionInvocationAsync(
        Kernel kernel,
        AutoFunctionInvocationContext context,
        Func<AutoFunctionInvocationContext, Task> functionCallCallback)
    {
        await InvokeFilterOrFunctionAsync(kernel.AutoFunctionInvocationFilters, functionCallCallback, context).ConfigureAwait(false);

        return context;
    }

    /// <summary>
    /// This method will execute auto function invocation filters and function recursively.
    /// If there are no registered filters, just function will be executed.
    /// If there are registered filters, filter on <paramref name="index"/> position will be executed.
    /// Second parameter of filter is callback. It can be either filter on <paramref name="index"/> + 1 position or function if there are no remaining filters to execute.
    /// Function will be always executed as last step after all filters.
    /// </summary>
    private static async Task InvokeFilterOrFunctionAsync(
        IList<IAutoFunctionInvocationFilter>? autoFunctionInvocationFilters,
        Func<AutoFunctionInvocationContext, Task> functionCallCallback,
        AutoFunctionInvocationContext context,
        int index = 0)
    {
        if (autoFunctionInvocationFilters is { Count: > 0 } && index < autoFunctionInvocationFilters.Count)
        {
            await autoFunctionInvocationFilters[index].OnAutoFunctionInvocationAsync(context,
                (context) => InvokeFilterOrFunctionAsync(autoFunctionInvocationFilters, functionCallCallback, context, index + 1)).ConfigureAwait(false);
        }
        else
        {
            await functionCallCallback(context).ConfigureAwait(false);
        }
    }

    private void AddBatchedToolResponseMessage(
        ChatHistory chat,
        GeminiRequest request,
        List<GeminiChatMessageContent> toolResponses)
    {
        if (toolResponses.Count == 0)
        {
            return;
        }

        // Extract all tool results and combine content
        var allToolResults = toolResponses
            .Where(tr => tr.CalledToolResults != null)
            .SelectMany(tr => tr.CalledToolResults!)
            .ToList();

        // Combine tool response content as a JSON array for better structure
        var combinedContentList = toolResponses
            .Select(tr => tr.Content)
            .Where(c => !string.IsNullOrEmpty(c))
            .ToList();

        var combinedContent = combinedContentList.Count switch
        {
            0 => string.Empty,
            1 => combinedContentList[0],
            _ => JsonSerializer.Serialize(combinedContentList)
        };

        // Create a single message with all function response parts using the new constructor
        var batchedMessage = new GeminiChatMessageContent(
            AuthorRole.Tool,
            combinedContent,
            this._modelId,
            calledToolResults: allToolResults);

        chat.Add(batchedMessage);
        request.AddChatMessage(batchedMessage);
    }

    private GeminiChatMessageContent CreateToolResponseMessage(
        GeminiFunctionToolCall tool,
        FunctionResult? functionResponse,
        string? errorMessage)
    {
        if (errorMessage is not null && this.Logger.IsEnabled(LogLevel.Debug))
        {
            this.Logger.LogDebug("Failed to handle tool request ({ToolName}). {Error}", tool.FullyQualifiedName, errorMessage);
        }

        return new GeminiChatMessageContent(AuthorRole.Tool,
            content: errorMessage ?? string.Empty,
            modelId: this._modelId,
            calledToolResult: functionResponse is not null ? new GeminiFunctionToolResult(tool, functionResponse) : null,
            metadata: null);
    }

    private async Task<GeminiResponse> SendRequestAndReturnValidGeminiResponseAsync(
        Uri endpoint,
        GeminiRequest geminiRequest,
        CancellationToken cancellationToken)
    {
        using var httpRequestMessage = await this.CreateHttpRequestAsync(geminiRequest, endpoint).ConfigureAwait(false);
        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        ValidateGeminiResponse(geminiResponse);
        return geminiResponse;
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(IEnumerable<GeminiTool.FunctionDeclaration> functions, GeminiFunctionToolCall ftc)
        => functions.Any(geminiFunction =>
            string.Equals(geminiFunction.Name, ftc.FullyQualifiedName, StringComparison.OrdinalIgnoreCase));

    private static bool CheckAutoInvokeCondition(Kernel? kernel, GeminiPromptExecutionSettings geminiExecutionSettings)
    {
        bool autoInvoke = kernel is not null
                          && geminiExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0
                          && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;
        ValidateAutoInvoke(autoInvoke, geminiExecutionSettings.CandidateCount ?? 1);
        return autoInvoke;
    }

    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);
        if (chatHistory.All(message => message.Role == AuthorRole.System))
        {
            throw new InvalidOperationException("Chat history can't contain only system messages.");
        }
    }

    private async IAsyncEnumerable<GeminiChatMessageContent> ProcessChatResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken ct)
    {
        await foreach (var response in this.ParseResponseStreamAsync(responseStream, ct: ct).ConfigureAwait(false))
        {
            foreach (var messageContent in this.ProcessChatResponse(response))
            {
                yield return messageContent;
            }
        }
    }

    private async IAsyncEnumerable<GeminiResponse> ParseResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken ct)
    {
        await foreach (var json in this._streamJsonParser.ParseAsync(responseStream, cancellationToken: ct).ConfigureAwait(false))
        {
            yield return DeserializeResponse<GeminiResponse>(json);
        }
    }

    private List<GeminiChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        ValidateGeminiResponse(geminiResponse);

        var chatMessageContents = this.GetChatMessageContentsFromResponse(geminiResponse);
        this.LogUsage(chatMessageContents);
        return chatMessageContents;
    }

    private static void ValidateGeminiResponse(GeminiResponse geminiResponse)
    {
        if (geminiResponse.PromptFeedback?.BlockReason is not null)
        {
            // TODO: Currently SK doesn't support prompt feedback/finish status, so we just throw an exception. I told SK team that we need to support it: https://github.com/microsoft/semantic-kernel/issues/4621
            throw new KernelException("Prompt was blocked due to Gemini API safety reasons.");
        }
    }

    private void LogUsage(List<GeminiChatMessageContent> chatMessageContents)
    {
        GeminiMetadata? metadata = chatMessageContents[0].Metadata;

        if (metadata is null || metadata.TotalTokenCount <= 0)
        {
            this.Logger.LogDebug("Token usage information unavailable.");
            return;
        }

        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation(
                "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}.",
                metadata.PromptTokenCount,
                metadata.CandidatesTokenCount,
                metadata.TotalTokenCount);
        }

        s_promptTokensCounter.Add(metadata.PromptTokenCount);
        s_completionTokensCounter.Add(metadata.CandidatesTokenCount);
        s_totalTokensCounter.Add(metadata.TotalTokenCount);
    }

    private List<GeminiChatMessageContent> GetChatMessageContentsFromResponse(GeminiResponse geminiResponse)
        => geminiResponse.Candidates == null ?
            [new GeminiChatMessageContent(role: AuthorRole.Assistant, content: string.Empty, modelId: this._modelId, functionsToolCalls: null)]
            : geminiResponse.Candidates.Select(candidate => this.GetChatMessageContentFromCandidate(geminiResponse, candidate)).ToList();

    private GeminiChatMessageContent GetChatMessageContentFromCandidate(GeminiResponse geminiResponse, GeminiResponseCandidate candidate)
    {
        var items = new List<KernelContent>();

        // Process parts to separate regular text from thinking content
        var regularTextParts = new List<string>();

        if (candidate.Content?.Parts != null)
        {
            foreach (var part in candidate.Content.Parts)
            {
                if (part.Thought == true && !string.IsNullOrEmpty(part.Text))
                {
                    // This is thinking content
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
                    items.Add(new ReasoningContent(part.Text));
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
                }
                else if (!string.IsNullOrEmpty(part.Text))
                {
                    // This is regular text content
                    regularTextParts.Add(part.Text);
                }
            }
        }

        // Regular text goes into message.Content, not as a separate item
        var regularText = string.Concat(regularTextParts);

        // Gemini sometimes returns function calls with text parts, so collect them
        // Use full GeminiPart[] to preserve ThoughtSignature for function calls with thinking enabled
        var partsWithFunctionCalls = candidate.Content?.Parts?
            .Where(part => part.FunctionCall is not null).ToArray();

        // For text responses (no function calls), capture ThoughtSignature from last part for metadata
        // Per Google docs: "The final content part returned by the model may contain a thought_signature"
        var lastPart = candidate.Content?.Parts?.LastOrDefault();
        var hasFunctionCalls = partsWithFunctionCalls is { Length: > 0 };
        string? textThoughtSignature = (!hasFunctionCalls && lastPart?.FunctionCall is null) ? lastPart?.ThoughtSignature : null;

        // Pass null if there's no regular (non-thinking) text to avoid creating an empty TextContent item
        var chatMessage = new GeminiChatMessageContent(
            role: candidate.Content?.Role ?? AuthorRole.Assistant,
            content: string.IsNullOrEmpty(regularText) ? null : regularText,
            modelId: this._modelId,
            partsWithFunctionCalls: partsWithFunctionCalls,
            metadata: GetResponseMetadata(geminiResponse, candidate, textThoughtSignature));

        // Add items to the message
        foreach (var item in items)
        {
            chatMessage.Items.Add(item);
        }

        return chatMessage;
    }

    private static GeminiRequest CreateRequest(
        ChatHistory chatHistory,
        GeminiPromptExecutionSettings geminiExecutionSettings,
        Kernel? kernel)
    {
        var geminiRequest = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, geminiExecutionSettings);
        geminiExecutionSettings.ToolCallBehavior?.ConfigureGeminiRequest(kernel, geminiRequest);
        return geminiRequest;
    }

    private GeminiStreamingChatMessageContent GetStreamingChatContentFromChatContent(GeminiChatMessageContent message)
    {
        GeminiStreamingChatMessageContent streamingMessage;

        if (message.CalledToolResult is not null)
        {
            streamingMessage = new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                calledToolResult: message.CalledToolResult,
                metadata: message.Metadata,
                choiceIndex: message.Metadata?.Index ?? 0);
        }
        else if (message.ToolCalls is not null)
        {
            streamingMessage = new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                toolCalls: message.ToolCalls,
                metadata: message.Metadata,
                choiceIndex: message.Metadata?.Index ?? 0);
        }
        else
        {
            streamingMessage = new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                choiceIndex: message.Metadata?.Index ?? 0,
                metadata: message.Metadata);
        }

        // Copy ReasoningContent items to streaming message, converting to StreamingReasoningContent
        foreach (var item in message.Items)
        {
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            if (item is ReasoningContent reasoningContent)
            {
                var streamingReasoning = new StreamingReasoningContent(reasoningContent.Text)
                {
                    InnerContent = reasoningContent.Text
                };
                streamingMessage.Items.Add(streamingReasoning);
            }
            // Note: Other item types like TextContent are not copied since the main content
            // is already in streamingMessage.Content
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        }

        return streamingMessage;
    }

    private static void ValidateAutoInvoke(bool autoInvoke, int resultsPerPrompt)
    {
        if (autoInvoke && resultsPerPrompt != 1)
        {
            // We can remove this restriction in the future if valuable. However, multiple results per prompt is rare,
            // and limiting this significantly curtails the complexity of the implementation.
            throw new ArgumentException(
                $"Auto-invocation of tool calls may only be used with a {nameof(GeminiPromptExecutionSettings.CandidateCount)} of 1.");
        }
    }

    private static GeminiMetadata GetResponseMetadata(
        GeminiResponse geminiResponse,
        GeminiResponseCandidate candidate,
        string? thoughtSignature = null) => new()
        {
            FinishReason = candidate.FinishReason,
            Index = candidate.Index,
            PromptTokenCount = geminiResponse.UsageMetadata?.PromptTokenCount ?? 0,
            CachedContentTokenCount = geminiResponse.UsageMetadata?.CachedContentTokenCount ?? 0,
            ThoughtsTokenCount = geminiResponse.UsageMetadata?.ThoughtsTokenCount ?? 0,
            CurrentCandidateTokenCount = candidate.TokenCount,
            CandidatesTokenCount = geminiResponse.UsageMetadata?.CandidatesTokenCount ?? 0,
            TotalTokenCount = geminiResponse.UsageMetadata?.TotalTokenCount ?? 0,
            PromptFeedbackBlockReason = geminiResponse.PromptFeedback?.BlockReason,
            PromptFeedbackSafetyRatings = geminiResponse.PromptFeedback?.SafetyRatings.ToList(),
            ResponseSafetyRatings = candidate.SafetyRatings?.ToList(),
            ThoughtSignature = thoughtSignature,
        };

    private sealed class ChatCompletionState
    {
        internal ChatHistory ChatHistory { get; set; } = null!;
        internal GeminiRequest GeminiRequest { get; set; } = null!;
        internal Kernel Kernel { get; set; } = null!;
        internal GeminiPromptExecutionSettings ExecutionSettings { get; set; } = null!;
        internal GeminiChatMessageContent? LastMessage { get; set; }
        internal int Iteration { get; set; }
        internal bool AutoInvoke { get; set; }
        internal bool FilterTerminationRequested { get; set; }

        internal void AddLastMessageToChatHistoryAndRequest()
        {
            Verify.NotNull(this.LastMessage);
            this.ChatHistory.Add(this.LastMessage);
            this.GeminiRequest.AddChatMessage(this.LastMessage);
        }
    }
}
