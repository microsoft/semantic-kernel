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
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
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
    private readonly FunctionCallsProcessor _functionCallsProcessor;

    private static readonly string s_namespace = typeof(GoogleAIGeminiChatCompletionService).Namespace!;

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

    private sealed record ToolCallingConfig(
        IList<GeminiTool.FunctionDeclaration>? Tools,
        GeminiFunctionCallingMode? Mode,
        bool AutoInvoke,
        FunctionChoiceBehaviorOptions? Options);

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
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._functionCallsProcessor = new FunctionCallsProcessor(this.Logger);
        this._chatGenerationEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._modelId}:generateContent?key={apiKey}");
        this._chatStreamingEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._modelId}:streamGenerateContent?key={apiKey}&alt=sse");
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
        Verify.NotNullOrWhiteSpace(projectId);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._functionCallsProcessor = new FunctionCallsProcessor(this.Logger);
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

        for (state.RequestIndex = 0;; state.RequestIndex++)
        {
            // TODO: do something with this variable
            var functionCallingConfig = this.GetFunctionCallingConfiguration(state);

            // TODO: Here should be request created not above loop

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
            if (!state.AutoInvoke || chatResponses.Count == 0)
            {
                return chatResponses;
            }

            state.LastMessage = chatResponses[0];
            // TODO: will ToolCalls property shoul be removed from GeminiChatMessageContent?
            if (state.LastMessage.ToolCalls is null)
            {
                return chatResponses;
            }

            // TODO: to remove?
            // state.AddLastMessageToChatHistoryAndRequest();

            // Process function calls by invoking the functions and adding the results to the chat history.
            // Each function call will trigger auto-function-invocation filters, which can terminate the process.
            // In such cases, we'll return the last message in the chat history.
            var lastMessage = await this._functionCallsProcessor.ProcessFunctionCallsAsync(
                state.LastMessage,
                chatHistory,
                state.RequestIndex,
                content => IsRequestableTool(state.LastMessage.ToolCalls, content),
                functionCallingConfig.Options ?? new FunctionChoiceBehaviorOptions(),
                kernel,
                isStreaming: false,
                cancellationToken).ConfigureAwait(false);

            if (lastMessage != null)
            {
                return [lastMessage];
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

        for (state.RequestIndex = 1;; state.RequestIndex++)
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
                    responseStream = await httpResponseMessage.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
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
        }
    }

    private ToolCallingConfig GetFunctionCallingConfiguration(ChatCompletionState state)
    {
        // If neither behavior is specified, we just return default configuration with no tool and no choice
        if (state.ExecutionSettings.FunctionChoiceBehavior is null)
        {
            return new ToolCallingConfig(Tools: null, Mode: null, AutoInvoke: false, Options: null);
        }

        return this.ConfigureFunctionCalling(state);
    }

    private ToolCallingConfig ConfigureFunctionCalling(ChatCompletionState state)
    {
        var config =
            this._functionCallsProcessor.GetConfiguration(state.ExecutionSettings.FunctionChoiceBehavior, state.ChatHistory, state.RequestIndex, state.Kernel);

        IList<GeminiTool.FunctionDeclaration>? tools = null;
        GeminiFunctionCallingMode? toolMode = null;
        bool autoInvoke = config?.AutoInvoke ?? false;

        if (config?.Functions is { Count: > 0 } functions)
        {
            if (config.Choice == FunctionChoice.Auto)
            {
                toolMode = GeminiFunctionCallingMode.Default;
            }
            else if (config.Choice == FunctionChoice.Required)
            {
                toolMode = GeminiFunctionCallingMode.Any;
            }
            else if (config.Choice == FunctionChoice.None)
            {
                toolMode = GeminiFunctionCallingMode.None;
            }
            else
            {
                throw new NotSupportedException($"Unsupported function choice '{config.Choice}'.");
            }

            tools = [];

            foreach (var function in functions)
            {
                tools.Add(function.Metadata.ToOpenAIFunction().ToFunctionDefinition());
            }
        }

        return new ToolCallingConfig(
            Tools: tools,
            Mode: toolMode ?? GeminiFunctionCallingMode.None,
            AutoInvoke: autoInvoke,
            Options: config?.Options);
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(IReadOnlyList<GeminiFunctionToolCall> tools, FunctionCallContent functionCallContent)
    {
        foreach (var tool in tools)
        {
            if (string.Equals(tool.FunctionName,
                    FunctionName.ToFullyQualifiedName(
                        functionCallContent.FunctionName,
                        functionCallContent.PluginName,
                        GeminiFunction.NameSeparator),
                    StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
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
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory),
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
                if (state.AutoInvoke && messageContent.ToolCalls is not null)
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
                    yield break;
                }

                // We disable auto-invoke because the first message in the stream doesn't contain ToolCalls or auto-invoke is already false
                state.AutoInvoke = false;

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
        foreach (var toolCall in state.LastMessage!.ToolCalls!)
        {
            await this.ProcessSingleToolCallAsync(state, toolCall, cancellationToken).ConfigureAwait(false);
        }

        // Clear the tools. If we end up wanting to use tools, we'll reset it to the desired value.
        state.GeminiRequest.Tools = null;

        if (state.RequestIndex >= state.ExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
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
        if (state.RequestIndex >= state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
        {
            state.AutoInvoke = false;
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.",
                    state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
            }
        }
    }

    private async Task ProcessSingleToolCallAsync(ChatCompletionState state, GeminiFunctionToolCall toolCall, CancellationToken cancellationToken)
    {
        // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
        // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
        // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
        if (state.ExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
            !IsRequestableTool(state.GeminiRequest.Tools![0].Functions, toolCall))
        {
            this.AddToolResponseMessage(state.ChatHistory, state.GeminiRequest, toolCall, functionResponse: null,
                "Error: Function call request for a function that wasn't defined.");
            return;
        }

        // Ensure the provided function exists for calling
        if (!state.Kernel!.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? functionArgs))
        {
            this.AddToolResponseMessage(state.ChatHistory, state.GeminiRequest, toolCall, functionResponse: null,
                "Error: Requested function could not be found.");
            return;
        }

        // Now, invoke the function, and add the resulting tool call message to the chat history.
        s_inflightAutoInvokes.Value++;
        FunctionResult? functionResult;
        try
        {
            // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
            // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
            // as the called function could in turn telling the model about itself as a possible candidate for invocation.
            functionResult = await function.InvokeAsync(state.Kernel, functionArgs, cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch (Exception e)
#pragma warning restore CA1031
        {
            this.AddToolResponseMessage(state.ChatHistory, state.GeminiRequest, toolCall, functionResponse: null,
                $"Error: Exception while invoking function. {e.Message}");
            return;
        }
        finally
        {
            s_inflightAutoInvokes.Value--;
        }

        this.AddToolResponseMessage(state.ChatHistory, state.GeminiRequest, toolCall,
            functionResponse: functionResult, errorMessage: null);
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

    private void AddToolResponseMessage(
        ChatHistory chat,
        GeminiRequest request,
        GeminiFunctionToolCall tool,
        FunctionResult? functionResponse,
        string? errorMessage)
    {
        if (errorMessage is not null && this.Logger.IsEnabled(LogLevel.Debug))
        {
            this.Logger.LogDebug("Failed to handle tool request ({ToolName}). {Error}", tool.FullyQualifiedName, errorMessage);
        }

        var message = new GeminiChatMessageContent(AuthorRole.Tool,
            content: errorMessage ?? string.Empty,
            modelId: this._modelId,
            calledToolResult: functionResponse is not null ? new(tool, functionResponse) : null,
            metadata: null);
        chat.Add(message);
        request.AddChatMessage(message);
    }

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
        => geminiResponse.Candidates == null
            ? [new GeminiChatMessageContent(role: AuthorRole.Assistant, content: string.Empty, modelId: this._modelId)]
            : geminiResponse.Candidates.Select(candidate => this.GetChatMessageContentFromCandidate(geminiResponse, candidate)).ToList();

    private GeminiChatMessageContent GetChatMessageContentFromCandidate(GeminiResponse geminiResponse, GeminiResponseCandidate candidate)
    {
        GeminiPart? part = candidate.Content?.Parts?[0];
        GeminiPart.FunctionCallPart[]? toolCalls = part?.FunctionCall is { } function ? [function] : null;
        return new GeminiChatMessageContent(
            role: candidate.Content?.Role ?? AuthorRole.Assistant,
            content: part?.Text ?? string.Empty,
            modelId: this._modelId,
            functionsToolCalls: toolCalls,
            metadata: GetResponseMetadata(geminiResponse, candidate));
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
        if (message.CalledToolResult is not null)
        {
            return new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                calledToolResult: message.CalledToolResult,
                metadata: message.Metadata,
                choiceIndex: message.Metadata?.Index ?? 0);
        }

        if (message.ToolCalls is not null)
        {
            return new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                toolCalls: message.ToolCalls,
                metadata: message.Metadata,
                choiceIndex: message.Metadata?.Index ?? 0);
        }

        return new GeminiStreamingChatMessageContent(
            role: message.Role,
            content: message.Content,
            modelId: this._modelId,
            choiceIndex: message.Metadata?.Index ?? 0,
            metadata: message.Metadata);
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
        GeminiResponseCandidate candidate) => new()
    {
        FinishReason = candidate.FinishReason,
        Index = candidate.Index,
        PromptTokenCount = geminiResponse.UsageMetadata?.PromptTokenCount ?? 0,
        CurrentCandidateTokenCount = candidate.TokenCount,
        CandidatesTokenCount = geminiResponse.UsageMetadata?.CandidatesTokenCount ?? 0,
        TotalTokenCount = geminiResponse.UsageMetadata?.TotalTokenCount ?? 0,
        PromptFeedbackBlockReason = geminiResponse.PromptFeedback?.BlockReason,
        PromptFeedbackSafetyRatings = geminiResponse.PromptFeedback?.SafetyRatings.ToList(),
        ResponseSafetyRatings = candidate.SafetyRatings?.ToList(),
    };

    private sealed class ChatCompletionState
    {
        internal ChatHistory ChatHistory { get; set; } = null!;
        internal GeminiRequest GeminiRequest { get; set; } = null!;
        internal Kernel Kernel { get; set; } = null!;
        internal GeminiPromptExecutionSettings ExecutionSettings { get; set; } = null!;
        internal GeminiChatMessageContent? LastMessage { get; set; }
        internal int RequestIndex { get; set; }
        internal bool AutoInvoke { get; set; }

        internal void AddLastMessageToChatHistoryAndRequest()
        {
            Verify.NotNull(this.LastMessage);
            this.ChatHistory.Add(this.LastMessage);
            this.GeminiRequest.AddChatMessage(this.LastMessage);
        }
    }
}
