// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a client for interacting with the chat completion gemini model.
/// </summary>
internal sealed class GeminiChatCompletionClient : ClientBase, IGeminiChatCompletionClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;
    private readonly Uri _chatGenerationEndpoint;
    private readonly Uri _chatStreamingEndpoint;

    private static readonly string s_namespace = typeof(GeminiChatCompletionClient).Namespace!;

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
    private const int MaxInflightAutoInvokes = 5;

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
    /// Represents a client for interacting with the chat completion gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._modelId = modelId;
        this._streamJsonParser = streamJsonParser ?? new GeminiStreamJsonParser();
        this._chatGenerationEndpoint = this.EndpointProvider.GetGeminiChatCompletionEndpoint(this._modelId);
        this._chatStreamingEndpoint = this.EndpointProvider.GetGeminiStreamChatCompletionEndpoint(this._modelId);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var state = CreateChatCompletionState(chatHistory, kernel, executionSettings);

        for (state.Iteration = 1; ; state.Iteration++)
        {
            var geminiResponse = await this.SendRequestAndReturnValidGeminiResponseAsync(
                    this._chatGenerationEndpoint, state.GeminiRequest, cancellationToken)
                .ConfigureAwait(false);

            var chatResponses = this.ProcessChatResponse(geminiResponse);

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!state.AutoInvoke || chatResponses.Count != 1)
            {
                return chatResponses;
            }

            state.LastMessage = chatResponses[0];
            if (state.LastMessage.ToolCalls is null)
            {
                return chatResponses;
            }

            state.AddLastMessageToChatHistoryAndRequest();
            await this.ProcessFunctionsAsync(state, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var state = CreateChatCompletionState(chatHistory, kernel, executionSettings);

        for (state.Iteration = 1; ; state.Iteration++)
        {
            using var httpRequestMessage = this.HttpRequestFactory.CreatePost(state.GeminiRequest, this._chatStreamingEndpoint);
            using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
                .ConfigureAwait(false);
            using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
                .ConfigureAwait(false);

            foreach (var messageContent in this.GetStreamingChatMessageContentsOrPopulateStateForToolCalling(state, responseStream))
            {
                yield return messageContent;
            }

            if (!state.AutoInvoke)
            {
                yield break;
            }

            state.AddLastMessageToChatHistoryAndRequest();
            await this.ProcessFunctionsAsync(state, cancellationToken).ConfigureAwait(false);
        }
    }

    private static ChatCompletionState CreateChatCompletionState(
        ChatHistory chatHistory,
        Kernel? kernel,
        PromptExecutionSettings? executionSettings)
    {
        var chatHistoryCopy = new ChatHistory(chatHistory);
        ValidateAndPrepareChatHistory(chatHistoryCopy);

        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);

        return new ChatCompletionState()
        {
            AutoInvoke = CheckAutoInvokeCondition(kernel, geminiExecutionSettings),
            ChatHistory = chatHistory,
            ExecutionSettings = geminiExecutionSettings,
            GeminiRequest = CreateRequest(chatHistoryCopy, geminiExecutionSettings, kernel),
            Kernel = kernel! // not null if auto-invoke is true
        };
    }

    private IEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsOrPopulateStateForToolCalling(
        ChatCompletionState state,
        Stream responseStream)
    {
        using var chatResponsesEnumerator = this.ProcessChatResponseStream(responseStream).GetEnumerator();
        while (chatResponsesEnumerator.MoveNext())
        {
            var messageContent = chatResponsesEnumerator.Current!;
            if (state.AutoInvoke && messageContent.ToolCalls is not null)
            {
                if (chatResponsesEnumerator.MoveNext())
                {
                    // We disable auto-invoke because we have more than one message in the stream.
                    // This scenario should not happen but I leave it as a precaution
                    state.AutoInvoke = false;
                    chatResponsesEnumerator.Reset();
                    continue;
                }

                // If function call was returned there is no more data in stream
                state.LastMessage = messageContent;
                yield break;
            }

            // We disable auto-invoke because the first message in the stream doesn't contain ToolCalls or auto-ivoke is already false
            state.AutoInvoke = false;

            // If we don't want to attempt to invoke any functions, just return the result.
            yield return this.GetStreamingChatContentFromChatContent(messageContent);
        }
    }

    private async Task ProcessFunctionsAsync(ChatCompletionState state, CancellationToken cancellationToken)
    {
        this.Logger.LogDebug("Tool requests: {Requests}", state.LastMessage!.ToolCalls!.Count);
        this.Logger.LogTrace("Function call requests: {FunctionCall}",
            string.Join(", ", state.LastMessage.ToolCalls.Select(ftc => ftc.ToString())));

        // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
        foreach (var toolCall in state.LastMessage.ToolCalls)
        {
            await this.ProcessSingleToolCallAsync(state, toolCall, cancellationToken).ConfigureAwait(false);
        }

        // If we've reached the maximum number of attempts for tools usage, we need to clear the tools
        if (state.Iteration >= state.ExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
        {
            // Clear the tools
            state.GeminiRequest.Tools = null;
            this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tools.",
                state.ExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
        }

        // If we've reached the maximum number of attempts for auto-invoke, we need to disable auto-invoke
        if (state.Iteration >= state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
        {
            state.AutoInvoke = false;
            this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.",
                state.ExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
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
        object? functionResult;
        try
        {
            // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
            // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
            // as the called function could in turn telling the model about itself as a possible candidate for invocation.
            functionResult = (await function.InvokeAsync(state.Kernel, functionArgs, cancellationToken: cancellationToken)
                .ConfigureAwait(false)).GetValue<object>() ?? string.Empty;
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
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, endpoint);
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

    private void AddToolResponseMessage(
        ChatHistory chat,
        GeminiRequest request,
        GeminiFunctionToolCall tool,
        object? functionResponse,
        string? errorMessage)
    {
        if (errorMessage is not null)
        {
            this.Logger.LogDebug("Failed to handle tool request ({ToolName}). {Error}", tool.FullyQualifiedName, errorMessage);
        }

        if (functionResponse is not null)
        {
            tool = new GeminiFunctionToolCall(tool, functionResponse);
        }

        var message = new GeminiChatMessageContent(AuthorRole.Tool,
            content: errorMessage ?? string.Empty,
            modelId: this._modelId, calledTool: tool, metadata: null);
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

    private static void ValidateAndPrepareChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);

        if (chatHistory.Where(message => message.Role == AuthorRole.System).ToList() is { Count: > 0 } systemMessages)
        {
            if (chatHistory.Count == systemMessages.Count)
            {
                throw new InvalidOperationException("Chat history can't contain only system messages.");
            }

            if (systemMessages.Count > 1)
            {
                throw new InvalidOperationException("Chat history can't contain more than one system message. " +
                                                    "Only the first system message will be processed but will be converted to the user message before sending to the Gemini api.");
            }

            ConvertSystemMessageToUserMessageInChatHistory(chatHistory, systemMessages[0]);
        }

        ValidateChatHistoryMessagesOrder(chatHistory);
    }

    private static void ConvertSystemMessageToUserMessageInChatHistory(ChatHistory chatHistory, ChatMessageContent systemMessage)
    {
        // TODO: This solution is needed due to the fact that Gemini API doesn't support system messages. Maybe in the future we will be able to remove it.
        chatHistory.Remove(systemMessage);
        if (!string.IsNullOrWhiteSpace(systemMessage.Content))
        {
            chatHistory.Insert(0, new ChatMessageContent(AuthorRole.User, systemMessage.Content));
            chatHistory.Insert(1, new ChatMessageContent(AuthorRole.Assistant, "OK"));
        }
    }

    private static void ValidateChatHistoryMessagesOrder(ChatHistory chatHistory)
    {
        bool incorrectOrder = false;
        // Exclude tool calls from the validation
        ChatHistory chatHistoryCopy = new(chatHistory
            .Where(message => message.Role != AuthorRole.Tool && (message is not GeminiChatMessageContent { ToolCalls: not null })));
        for (int i = 0; i < chatHistoryCopy.Count; i++)
        {
            if (chatHistoryCopy[i].Role != (i % 2 == 0 ? AuthorRole.User : AuthorRole.Assistant) ||
                (i == chatHistoryCopy.Count - 1 && chatHistoryCopy[i].Role != AuthorRole.User))
            {
                incorrectOrder = true;
                break;
            }
        }

        if (incorrectOrder)
        {
            throw new NotSupportedException(
                "Gemini API support only chat history with order of messages alternates between the user and the assistant. " +
                "Last message have to be User message.");
        }
    }

    private IEnumerable<GeminiChatMessageContent> ProcessChatResponseStream(Stream responseStream)
        => from geminiResponse in this.ParseResponseStream(responseStream)
           from chatMessageContent in this.ProcessChatResponse(geminiResponse)
           select chatMessageContent;

    private IEnumerable<GeminiResponse> ParseResponseStream(Stream responseStream)
        => this._streamJsonParser.Parse(responseStream).Select(DeserializeResponse<GeminiResponse>);

    private List<GeminiChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        ValidateGeminiResponse(geminiResponse);

        var chatMessageContents = this.GetChatMessageContentsFromResponse(geminiResponse);
        this.LogUsage(chatMessageContents);
        return chatMessageContents;
    }

    private static void ValidateGeminiResponse(GeminiResponse geminiResponse)
    {
        if (geminiResponse.Candidates == null || geminiResponse.Candidates.Count == 0 ||
            geminiResponse.Candidates.All(c => c.Content?.Parts == null))
        {
            if (geminiResponse.PromptFeedback?.BlockReason != null)
            {
                // TODO: Currently SK doesn't support prompt feedback/finish status, so we just throw an exception. I told SK team that we need to support it: https://github.com/microsoft/semantic-kernel/issues/4621
                throw new KernelException("Prompt was blocked due to Gemini API safety reasons.");
            }

            throw new KernelException("Gemini API doesn't return any data.");
        }
    }

    private void LogUsage(IReadOnlyList<ChatMessageContent> chatMessageContents)
        => this.LogUsageMetadata((GeminiMetadata)chatMessageContents[0].Metadata!);

    private List<GeminiChatMessageContent> GetChatMessageContentsFromResponse(GeminiResponse geminiResponse)
        => geminiResponse.Candidates!.Select(candidate => this.GetChatMessageContentFromCandidate(geminiResponse, candidate)).ToList();

    private GeminiChatMessageContent GetChatMessageContentFromCandidate(GeminiResponse geminiResponse, GeminiResponseCandidate candidate)
    {
        GeminiPart? part = candidate.Content?.Parts?[0];
        GeminiPart.FunctionCallPart[]? toolCalls = part?.FunctionCall is { } function ? new[] { function } : null;
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
        if (message.CalledTool != null)
        {
            return new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                calledTool: message.CalledTool,
                metadata: message.Metadata,
                choiceIndex: message.Metadata!.Index);
        }

        if (message.ToolCalls != null)
        {
            return new GeminiStreamingChatMessageContent(
                role: message.Role,
                content: message.Content,
                modelId: this._modelId,
                toolCalls: message.ToolCalls,
                metadata: message.Metadata,
                choiceIndex: message.Metadata!.Index);
        }

        return new GeminiStreamingChatMessageContent(
            role: message.Role,
            content: message.Content,
            modelId: this._modelId,
            choiceIndex: message.Metadata!.Index,
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

    private void LogUsageMetadata(GeminiMetadata metadata)
    {
        if (metadata.TotalTokenCount <= 0)
        {
            this.Logger.LogDebug("Gemini usage information is not available.");
            return;
        }

        this.Logger.LogDebug(
            "Gemini usage metadata: Candidates tokens: {CandidatesTokens}, Prompt tokens: {PromptTokens}, Total tokens: {TotalTokens}",
            metadata.CandidatesTokenCount,
            metadata.PromptTokenCount,
            metadata.TotalTokenCount);

        s_promptTokensCounter.Add(metadata.PromptTokenCount);
        s_completionTokensCounter.Add(metadata.CandidatesTokenCount);
        s_totalTokensCounter.Add(metadata.TotalTokenCount);
    }

    private sealed class ChatCompletionState
    {
        public ChatHistory ChatHistory { get; set; } = null!;
        public GeminiRequest GeminiRequest { get; set; } = null!;
        public Kernel Kernel { get; set; } = null!;
        public GeminiPromptExecutionSettings ExecutionSettings { get; set; } = null!;
        public GeminiChatMessageContent? LastMessage { get; set; }
        public int Iteration { get; set; }
        public bool AutoInvoke { get; set; }

        public void AddLastMessageToChatHistoryAndRequest()
        {
            Verify.NotNull(this.LastMessage);
            this.ChatHistory.Add(this.LastMessage);
            this.GeminiRequest.AddChatMessage(this.LastMessage);
        }
    }
}
