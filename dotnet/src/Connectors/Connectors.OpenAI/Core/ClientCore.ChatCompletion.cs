// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;
using OpenAI.Chat;
using OAIChat = OpenAI.Chat;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
#if NET
    [GeneratedRegex("[^a-zA-Z0-9_-]")]
    private static partial Regex DisallowedFunctionNameCharactersRegex();
#else
    private static Regex DisallowedFunctionNameCharactersRegex() => new("[^a-zA-Z0-9_-]", RegexOptions.Compiled);
#endif

    protected const string ModelProvider = "openai";
    protected record ToolCallingConfig(IList<ChatTool>? Tools, ChatToolChoice? Choice, bool AutoInvoke, bool AllowAnyRequestedKernelFunction, FunctionChoiceBehaviorOptions? Options);

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
    /// prompt function could advertize itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    protected const int MaxInflightAutoInvokes = 128;

    /// <summary>Singleton tool used when tool call count drops to 0 but we need to supply tools to keep the service happy.</summary>
    protected static readonly ChatTool s_nonInvocableFunctionTool = ChatTool.CreateFunctionTool("NonInvocableTool");

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    protected static readonly Meter s_meter = new("Microsoft.SemanticKernel.Connectors.OpenAI");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    protected static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    protected static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    protected static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    protected virtual Dictionary<string, object?> GetChatCompletionMetadata(OAIChat.ChatCompletion completions)
    {
        return new Dictionary<string, object?>
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.CreatedAt), completions.CreatedAt },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
            { nameof(completions.Usage), completions.Usage },
            { nameof(completions.Refusal), completions.Refusal },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completions.FinishReason), completions.FinishReason.ToString() },
            { nameof(completions.ContentTokenLogProbabilities), completions.ContentTokenLogProbabilities },
        };
    }

    protected static Dictionary<string, object?> GetChatCompletionMetadata(StreamingChatCompletionUpdate completionUpdate)
    {
        return new Dictionary<string, object?>
        {
            { nameof(completionUpdate.CompletionId), completionUpdate.CompletionId },
            { nameof(completionUpdate.CreatedAt), completionUpdate.CreatedAt },
            { nameof(completionUpdate.SystemFingerprint), completionUpdate.SystemFingerprint },
            { nameof(completionUpdate.RefusalUpdate), completionUpdate.RefusalUpdate },
            { nameof(completionUpdate.Usage), completionUpdate.Usage },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completionUpdate.FinishReason), completionUpdate.FinishReason?.ToString() },
        };
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="targetModel">Model identifier</param>
    /// <param name="chatHistory">Chat history</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Generated chat message in string format</returns>
    internal async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        string targetModel,
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        // Convert the incoming execution settings to OpenAI settings.
        OpenAIPromptExecutionSettings chatExecutionSettings = this.GetSpecializedExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        for (int requestIndex = 0; ; requestIndex++)
        {
            var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chatHistory);

            var functionCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, requestIndex);

            var chatOptions = this.CreateChatCompletionOptions(chatExecutionSettings, chatHistory, functionCallingConfig, kernel);

            // Make the request.
            OAIChat.ChatCompletion? chatCompletion = null;
            OpenAIChatMessageContent chatMessageContent;
            using (var activity = this.StartCompletionActivity(chatHistory, chatExecutionSettings))
            {
                try
                {
                    chatCompletion = (await RunRequestAsync(() => this.Client!.GetChatClient(targetModel).CompleteChatAsync(chatForRequest, chatOptions, cancellationToken)).ConfigureAwait(false)).Value;

                    this.LogUsage(chatCompletion.Usage);
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    if (chatCompletion != null)
                    {
                        // Capture available metadata even if the operation failed.
                        activity
                            .SetResponseId(chatCompletion.Id)
                            .SetInputTokensUsage(chatCompletion.Usage.InputTokenCount)
                            .SetOutputTokensUsage(chatCompletion.Usage.OutputTokenCount);
                    }

                    throw;
                }

                chatMessageContent = this.CreateChatMessageContent(chatCompletion, targetModel, functionCallingConfig.Options?.RetainArgumentTypes ?? false, chatOptions);
                activity?.SetCompletionResponse([chatMessageContent], chatCompletion.Usage.InputTokenCount, chatCompletion.Usage.OutputTokenCount);
            }

            // If we don't want to attempt to invoke any functions or there is nothing to call, just return the result.
            if (!functionCallingConfig.AutoInvoke || chatCompletion.ToolCalls.Count == 0)
            {
                return [chatMessageContent];
            }

            // Process function calls by invoking the functions and adding the results to the chat history.
            // Each function call will trigger auto-function-invocation filters, which can terminate the process.
            // In such cases, we'll return the last message in the chat history.
            var lastMessage = await this.FunctionCallsProcessor.ProcessFunctionCallsAsync(
                chatMessageContent,
                chatExecutionSettings,
                chatHistory,
                requestIndex,
                (FunctionCallContent content) => IsRequestableTool(chatOptions.Tools, content),
                functionCallingConfig.Options ?? new FunctionChoiceBehaviorOptions(),
                kernel,
                isStreaming: false,
                cancellationToken).ConfigureAwait(false);

            if (lastMessage != null)
            {
                return [lastMessage];
            }

            // Process non-function tool calls.
            this.ProcessNonFunctionToolCalls(chatCompletion.ToolCalls, chatHistory);
        }
    }

    internal async IAsyncEnumerable<OpenAIStreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        string targetModel,
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        OpenAIPromptExecutionSettings chatExecutionSettings = this.GetSpecializedExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;

        for (int requestIndex = 0; ; requestIndex++)
        {
            var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chatHistory);

            var functionCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, requestIndex);

            var chatOptions = this.CreateChatCompletionOptions(chatExecutionSettings, chatHistory, functionCallingConfig, kernel);

            // Reset state
            contentBuilder?.Clear();
            toolCallIdsByIndex?.Clear();
            functionNamesByIndex?.Clear();
            functionArgumentBuildersByIndex?.Clear();

            // Stream the response.
            IReadOnlyDictionary<string, object?>? metadata = null;
            string? streamedName = null;
            ChatMessageRole? streamedRole = default;
            ChatFinishReason finishReason = default;
            ChatToolCall[]? toolCalls = null;
            FunctionCallContent[]? functionCallContents = null;

            using (var activity = this.StartCompletionActivity(chatHistory, chatExecutionSettings))
            {
                // Make the request.
                AsyncCollectionResult<StreamingChatCompletionUpdate> response;
                try
                {
                    response = RunRequest(() => this.Client!.GetChatClient(targetModel).CompleteChatStreamingAsync(chatForRequest, chatOptions, cancellationToken));
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    throw;
                }

                var responseEnumerator = response.ConfigureAwait(false).GetAsyncEnumerator();
                List<OpenAIStreamingChatMessageContent>? streamedContents = activity is not null ? [] : null;
                try
                {
                    while (true)
                    {
                        try
                        {
                            if (!await responseEnumerator.MoveNextAsync())
                            {
                                break;
                            }
                        }
                        catch (Exception ex) when (activity is not null)
                        {
                            activity.SetError(ex);
                            throw;
                        }

                        StreamingChatCompletionUpdate chatCompletionUpdate = responseEnumerator.Current;
                        metadata = GetChatCompletionMetadata(chatCompletionUpdate);
                        streamedRole ??= chatCompletionUpdate.Role;
                        //streamedName ??= update.AuthorName;
                        finishReason = chatCompletionUpdate.FinishReason ?? default;

                        // If we're intending to invoke function calls, we need to consume that function call information.
                        if (functionCallingConfig.AutoInvoke)
                        {
                            foreach (var contentPart in chatCompletionUpdate.ContentUpdate)
                            {
                                if (contentPart.Kind == ChatMessageContentPartKind.Text)
                                {
                                    (contentBuilder ??= new()).Append(contentPart.Text);
                                }
                            }
                            OpenAIFunctionToolCall.TrackStreamingToolingUpdate(chatCompletionUpdate.ToolCallUpdates, ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);
                        }

                        var openAIStreamingChatMessageContent = new OpenAIStreamingChatMessageContent(chatCompletionUpdate, 0, targetModel, metadata);

                        if (openAIStreamingChatMessageContent.ToolCallUpdates is not null)
                        {
                            foreach (var functionCallUpdate in openAIStreamingChatMessageContent.ToolCallUpdates!)
                            {
                                // Using the code below to distinguish and skip non - function call related updates.
                                // The Kind property of updates can't be reliably used because it's only initialized for the first update.
                                if (string.IsNullOrEmpty(functionCallUpdate.ToolCallId) &&
                                    string.IsNullOrEmpty(functionCallUpdate.FunctionName) &&
                                    (functionCallUpdate.FunctionArgumentsUpdate is null || functionCallUpdate.FunctionArgumentsUpdate.ToMemory().IsEmpty))
                                {
                                    continue;
                                }

                                string streamingArguments = (functionCallUpdate.FunctionArgumentsUpdate?.ToMemory().IsEmpty ?? true)
                                    ? string.Empty
                                    : functionCallUpdate.FunctionArgumentsUpdate.ToString();

                                openAIStreamingChatMessageContent.Items.Add(new StreamingFunctionCallUpdateContent(
                                    callId: functionCallUpdate.ToolCallId,
                                    name: functionCallUpdate.FunctionName,
                                    arguments: streamingArguments,
                                    functionCallIndex: functionCallUpdate.Index)
                                {
                                    RequestIndex = requestIndex,
                                });
                            }
                        }
                        streamedContents?.Add(openAIStreamingChatMessageContent);
                        yield return openAIStreamingChatMessageContent;
                    }

                    // Translate all entries into ChatCompletionsFunctionToolCall instances.
                    toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToFunctionToolCalls(
                        ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);

                    // Translate all entries into FunctionCallContent instances for diagnostics purposes.
                    functionCallContents = this.GetFunctionCallContents(toolCalls, functionCallingConfig.Options?.RetainArgumentTypes ?? false).ToArray();
                }
                finally
                {
                    activity?.EndStreaming(streamedContents, ModelDiagnostics.IsSensitiveEventsEnabled() ? functionCallContents : null);
                    await responseEnumerator.DisposeAsync();
                }
            }

            // If we don't have a function to invoke, we're done.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            if (!functionCallingConfig.AutoInvoke ||
                toolCallIdsByIndex is not { Count: > 0 })
            {
                yield break;
            }

            // Get any response content that was streamed.
            string content = contentBuilder?.ToString() ?? string.Empty;

            var chatMessageContent = this.CreateChatMessageContent(streamedRole ?? default, content, toolCalls, functionCallContents, metadata, streamedName);

            // Process function calls by invoking the functions and adding the results to the chat history.
            // Each function call will trigger auto-function-invocation filters, which can terminate the process.
            // In such cases, we'll return the last message in the chat history.
            var lastMessage = await this.FunctionCallsProcessor.ProcessFunctionCallsAsync(
                chatMessageContent,
                chatExecutionSettings,
                chatHistory,
                requestIndex,
                (FunctionCallContent content) => IsRequestableTool(chatOptions.Tools, content),
                functionCallingConfig.Options ?? new FunctionChoiceBehaviorOptions(),
                kernel,
                isStreaming: true,
                cancellationToken).ConfigureAwait(false);

            if (lastMessage != null)
            {
                yield return new OpenAIStreamingChatMessageContent(lastMessage.Role, lastMessage.Content);
                yield break;
            }

            // Process non-function tool calls.
            this.ProcessNonFunctionToolCalls(toolCalls, chatHistory);
        }
    }

    internal async IAsyncEnumerable<StreamingTextContent> GetChatAsTextStreamingContentsAsync(
        string targetModel,
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatSettings = this.GetSpecializedExecutionSettings(executionSettings);
        ChatHistory chat = CreateNewChat(prompt, chatSettings);

        await foreach (var chatUpdate in this.GetStreamingChatMessageContentsAsync(targetModel, chat, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(chatUpdate.Content, chatUpdate.ChoiceIndex, chatUpdate.ModelId, chatUpdate, Encoding.UTF8, chatUpdate.Metadata);
        }
    }

    internal async Task<IReadOnlyList<TextContent>> GetChatAsTextContentsAsync(
        string model,
        string text,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatSettings = this.GetSpecializedExecutionSettings(executionSettings);

        ChatHistory chat = CreateNewChat(text, chatSettings);
        return (await this.GetChatMessageContentsAsync(model, chat, chatSettings, kernel, cancellationToken).ConfigureAwait(false))
            .Select(chat => new TextContent(chat.Content, chat.ModelId, chat.Content, Encoding.UTF8, chat.Metadata))
            .ToList();
    }

    /// <summary>
    /// Returns a specialized execution settings object for the OpenAI chat completion service.
    /// </summary>
    /// <param name="executionSettings">Potential execution settings infer specialized.</param>
    /// <returns>Specialized settings</returns>
    protected virtual OpenAIPromptExecutionSettings GetSpecializedExecutionSettings(PromptExecutionSettings? executionSettings)
        => OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

    /// <summary>
    /// Start a chat completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    protected virtual Activity? StartCompletionActivity(ChatHistory chatHistory, PromptExecutionSettings settings)
        => ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.ModelId, ModelProvider, chatHistory, settings);

    protected virtual ChatCompletionOptions CreateChatCompletionOptions(
        OpenAIPromptExecutionSettings executionSettings,
        ChatHistory chatHistory,
        ToolCallingConfig toolCallingConfig,
        Kernel? kernel)
    {
        var options = new ChatCompletionOptions
        {
            WebSearchOptions = GetWebSearchOptions(executionSettings),
            MaxOutputTokenCount = executionSettings.MaxTokens,
            Temperature = (float?)executionSettings.Temperature,
            TopP = (float?)executionSettings.TopP,
            FrequencyPenalty = (float?)executionSettings.FrequencyPenalty,
            PresencePenalty = (float?)executionSettings.PresencePenalty,
#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            Seed = executionSettings.Seed,
#pragma warning restore OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            EndUserId = executionSettings.User,
            TopLogProbabilityCount = executionSettings.TopLogprobs,
            IncludeLogProbabilities = executionSettings.Logprobs,
            StoredOutputEnabled = executionSettings.Store,
            ReasoningEffortLevel = GetEffortLevel(executionSettings),
        };

        // Set response modalities if specified in the execution settings
        if (executionSettings.Modalities is not null)
        {
            options.ResponseModalities = GetResponseModalities(executionSettings);
        }

        // Set audio options if specified in the execution settings
        if (executionSettings.Audio is not null)
        {
            options.AudioOptions = GetAudioOptions(executionSettings);
        }

        var responseFormat = GetResponseFormat(executionSettings);
        if (responseFormat is not null)
        {
            options.ResponseFormat = responseFormat;
        }

        if (toolCallingConfig.Choice is not null)
        {
            options.ToolChoice = toolCallingConfig.Choice;
        }

        if (toolCallingConfig.Tools is { Count: > 0 } tools)
        {
            options.Tools.AddRange(tools);
        }

        if (executionSettings.TokenSelectionBiases is not null)
        {
            foreach (var keyValue in executionSettings.TokenSelectionBiases)
            {
                options.LogitBiases.Add(keyValue.Key, keyValue.Value);
            }
        }

        if (executionSettings.StopSequences is { Count: > 0 })
        {
            foreach (var s in executionSettings.StopSequences)
            {
                options.StopSequences.Add(s);
            }
        }

        if (toolCallingConfig.Options?.AllowParallelCalls is not null)
        {
            options.AllowParallelToolCalls = toolCallingConfig.Options.AllowParallelCalls;
        }

        if (executionSettings.Metadata is not null)
        {
            foreach (var kvp in executionSettings.Metadata)
            {
                options.Metadata.Add(kvp.Key, kvp.Value);
            }
        }

        return options;
    }

    protected static ChatReasoningEffortLevel? GetEffortLevel(OpenAIPromptExecutionSettings executionSettings)
    {
        var effortLevelObject = executionSettings.ReasoningEffort;
        if (effortLevelObject is null)
        {
            return null;
        }

        if (effortLevelObject is ChatReasoningEffortLevel effort)
        {
            return effort;
        }

        if (effortLevelObject is string textEffortLevel)
        {
            return textEffortLevel.ToUpperInvariant() switch
            {
                "LOW" => ChatReasoningEffortLevel.Low,
                "MEDIUM" => ChatReasoningEffortLevel.Medium,
                "HIGH" => ChatReasoningEffortLevel.High,
                _ => throw new NotSupportedException($"The provided reasoning effort '{textEffortLevel}' is not supported.")
            };
        }

        throw new NotSupportedException($"The provided reasoning effort '{effortLevelObject.GetType()}' is not supported.");
    }

    protected static ChatWebSearchOptions? GetWebSearchOptions(OpenAIPromptExecutionSettings executionSettings)
    {
        if (executionSettings.WebSearchOptions is null)
        {
            return null;
        }

        if (executionSettings.WebSearchOptions is ChatWebSearchOptions webSearchOptions)
        {
            return webSearchOptions;
        }

        if (executionSettings.WebSearchOptions is string webSearchOptionsString)
        {
            return ModelReaderWriter.Read<ChatWebSearchOptions>(BinaryData.FromString(webSearchOptionsString));
        }

        if (executionSettings.WebSearchOptions is JsonElement webSearchOptionsElement)
        {
            return ModelReaderWriter.Read<ChatWebSearchOptions>(BinaryData.FromString(webSearchOptionsElement.GetRawText()));
        }

        throw new NotSupportedException($"The provided web search options '{executionSettings.WebSearchOptions.GetType()}' is not supported.");
    }

    /// <summary>
    /// Retrieves the response format based on the provided settings.
    /// </summary>
    /// <param name="executionSettings">Execution settings.</param>
    /// <returns>Chat response format</returns>
    protected static ChatResponseFormat? GetResponseFormat(OpenAIPromptExecutionSettings executionSettings)
    {
        switch (executionSettings.ResponseFormat)
        {
            case ChatResponseFormat formatObject:
                // If the response format is an OpenAI SDK ChatCompletionsResponseFormat, just pass it along.
                return formatObject;
            case string formatString:
                // If the response format is a string, map the ones we know about, and ignore the rest.
                switch (formatString)
                {
                    case "json_object":
                        return ChatResponseFormat.CreateJsonObjectFormat();

                    case "text":
                        return ChatResponseFormat.CreateTextFormat();
                }

                break;

            case JsonElement formatElement:
                // This is a workaround for a type mismatch when deserializing a JSON into an object? type property.
                if (formatElement.ValueKind == JsonValueKind.String)
                {
                    switch (formatElement.GetString())
                    {
                        case "json_object":
                            return ChatResponseFormat.CreateJsonObjectFormat();

                        case null:
                        case "":
                        case "text":
                            return ChatResponseFormat.CreateTextFormat();
                    }
                }

                return OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(formatElement);

            case Type formatObjectType:
                return OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(formatObjectType);
        }

        return null;
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(IList<ChatTool> tools, FunctionCallContent functionCallContent)
    {
        for (int i = 0; i < tools.Count; i++)
        {
            if (tools[i].Kind == ChatToolKind.Function &&
                string.Equals(tools[i].FunctionName, FunctionName.ToFullyQualifiedName(functionCallContent.FunctionName, functionCallContent.PluginName, OpenAIFunction.NameSeparator), StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Create a new empty chat instance
    /// </summary>
    /// <param name="text">Optional chat instructions for the AI service</param>
    /// <param name="executionSettings">Execution settings</param>
    /// <param name="textRole">Indicates what will be the role of the text. Defaults to system role prompt</param>
    /// <returns>Chat object</returns>
    private static ChatHistory CreateNewChat(string? text = null, OpenAIPromptExecutionSettings? executionSettings = null, AuthorRole? textRole = null)
    {
        var chat = new ChatHistory();

        // If settings is not provided, create a new chat with the text as the system prompt
        textRole ??= AuthorRole.System;

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatSystemPrompt))
        {
            chat.AddSystemMessage(executionSettings!.ChatSystemPrompt!);
            textRole = AuthorRole.User;
        }

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatDeveloperPrompt))
        {
            chat.AddDeveloperMessage(executionSettings!.ChatDeveloperPrompt!);
            textRole = AuthorRole.User;
        }

        if (!string.IsNullOrWhiteSpace(text))
        {
            chat.AddMessage(textRole.Value, text!);
        }

        return chat;
    }

    private static List<ChatMessage> CreateChatCompletionMessages(OpenAIPromptExecutionSettings executionSettings, ChatHistory chatHistory)
    {
        List<ChatMessage> messages = [];

        if (!string.IsNullOrWhiteSpace(executionSettings.ChatDeveloperPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.Developer))
        {
            messages.Add(new DeveloperChatMessage(executionSettings.ChatDeveloperPrompt));
        }

        if (!string.IsNullOrWhiteSpace(executionSettings.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            messages.Add(new SystemChatMessage(executionSettings.ChatSystemPrompt));
        }

        foreach (var message in chatHistory)
        {
            messages.AddRange(CreateRequestMessages(message));
        }

        return messages;
    }

    private static List<ChatMessage> CreateRequestMessages(ChatMessageContent message)
    {
        if (message.Role == AuthorRole.Developer)
        {
            return [new DeveloperChatMessage(message.Content) { ParticipantName = message.AuthorName }];
        }

        if (message.Role == AuthorRole.System)
        {
            return [new SystemChatMessage(message.Content) { ParticipantName = message.AuthorName }];
        }

        if (message.Role == AuthorRole.Tool)
        {
            // Handling function results represented by the TextContent type.
            // Example: new ChatMessageContent(AuthorRole.Tool, content, metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } })
            if (message.Metadata?.TryGetValue(OpenAIChatMessageContent.ToolIdProperty, out object? toolId) is true &&
                toolId?.ToString() is string toolIdString)
            {
                return [new ToolChatMessage(toolIdString, message.Content)];
            }

            // Handling function results represented by the FunctionResultContent type.
            // Example: new ChatMessageContent(AuthorRole.Tool, items: new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) })
            List<ChatMessage>? toolMessages = null;
            foreach (var item in message.Items)
            {
                if (item is not FunctionResultContent resultContent)
                {
                    continue;
                }

                toolMessages ??= [];

                if (resultContent.Result is Exception ex)
                {
                    toolMessages.Add(new ToolChatMessage(resultContent.CallId, $"Error: Exception while invoking function. {ex.Message}"));
                    continue;
                }

                var stringResult = FunctionCalling.FunctionCallsProcessor.ProcessFunctionResult(resultContent.Result ?? string.Empty);

                toolMessages.Add(new ToolChatMessage(resultContent.CallId, stringResult ?? string.Empty));
            }

            if (toolMessages is not null)
            {
                return toolMessages;
            }

            throw new NotSupportedException("No function result provided in the tool message.");
        }

        if (message.Role == AuthorRole.User)
        {
            if (message.Items is { Count: 1 } && message.Items.FirstOrDefault() is TextContent textContent)
            {
                return [new UserChatMessage(textContent.Text) { ParticipantName = message.AuthorName }];
            }

            return
            [
                new UserChatMessage(message.Items.Select(static (KernelContent item) => item switch
                    {
                        TextContent textContent => ChatMessageContentPart.CreateTextPart(textContent.Text),
                        ImageContent imageContent => GetImageContentItem(imageContent),
                        AudioContent audioContent => GetAudioContentItem(audioContent),
                        _ => throw new NotSupportedException($"Unsupported chat message content type '{item.GetType()}'.")
                    }))
                { ParticipantName = message.AuthorName }
            ];
        }

        if (message.Role == AuthorRole.Assistant)
        {
            var toolCalls = new List<ChatToolCall>();

            // Handling function calls supplied via either:
            // ChatCompletionsToolCall.ToolCalls collection items or
            // ChatMessageContent.Metadata collection item with 'ChatResponseMessage.FunctionToolCalls' key.
            IEnumerable<ChatToolCall>? tools = (message as OpenAIChatMessageContent)?.ToolCalls;
            if (tools is null && message.Metadata?.TryGetValue(OpenAIChatMessageContent.FunctionToolCallsProperty, out object? toolCallsObject) is true)
            {
                tools = toolCallsObject as IEnumerable<ChatToolCall>;
                if (tools is null && toolCallsObject is JsonElement { ValueKind: JsonValueKind.Array } array)
                {
                    int length = array.GetArrayLength();
                    var ftcs = new List<ChatToolCall>(length);
                    for (int i = 0; i < length; i++)
                    {
                        JsonElement e = array[i];
                        if (e.TryGetProperty("Id", out JsonElement id) &&
                            e.TryGetProperty("Name", out JsonElement name) &&
                            e.TryGetProperty("Arguments", out JsonElement arguments) &&
                            id.ValueKind == JsonValueKind.String &&
                            name.ValueKind == JsonValueKind.String &&
                            arguments.ValueKind == JsonValueKind.String)
                        {
                            ftcs.Add(ChatToolCall.CreateFunctionToolCall(id.GetString()!, name.GetString()!, BinaryData.FromString(arguments.GetString()!)));
                        }
                    }
                    tools = ftcs;
                }
            }

            if (tools is not null)
            {
                toolCalls.AddRange(tools);
            }

            // Handling function calls supplied via ChatMessageContent.Items collection elements of the FunctionCallContent type.
            HashSet<string>? functionCallIds = null;
            foreach (var item in message.Items)
            {
                if (item is not FunctionCallContent callRequest)
                {
                    continue;
                }

                functionCallIds ??= new HashSet<string>(toolCalls.Select(t => t.Id));

                if (callRequest.Id is null || functionCallIds.Contains(callRequest.Id))
                {
                    continue;
                }

                var argument = JsonSerializer.Serialize(callRequest.Arguments);

                toolCalls.Add(ChatToolCall.CreateFunctionToolCall(callRequest.Id, FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OpenAIFunction.NameSeparator), BinaryData.FromString(argument ?? string.Empty)));
            }

            // This check is necessary to prevent an exception that will be thrown if the toolCalls collection is empty.
            // HTTP 400 (invalid_request_error:) [] should be non-empty - 'messages.3.tool_calls'
            if (toolCalls.Count == 0)
            {
                return [new AssistantChatMessage(message.Content) { ParticipantName = message.AuthorName }];
            }

            var assistantMessage = new AssistantChatMessage(SanitizeFunctionNames(toolCalls)) { ParticipantName = message.AuthorName };

            // If message content is null, adding it as empty string,
            // because chat message content must be string.
            assistantMessage.Content.Add(message.Content ?? string.Empty);

            return [assistantMessage];
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static ChatMessageContentPart GetImageContentItem(ImageContent imageContent)
    {
        ChatImageDetailLevel? detailLevel = GetChatImageDetailLevel(imageContent);

        if (imageContent.Data is { IsEmpty: false } data)
        {
            return ChatMessageContentPart.CreateImagePart(BinaryData.FromBytes(data), imageContent.MimeType, detailLevel);
        }

        if (imageContent.Uri is not null)
        {
            return ChatMessageContentPart.CreateImagePart(imageContent.Uri, detailLevel);
        }

        throw new ArgumentException($"{nameof(ImageContent)} must have either Data or a Uri.");
    }

    private static ChatMessageContentPart GetAudioContentItem(AudioContent audioContent)
    {
        if (audioContent.Data is { IsEmpty: false } data)
        {
            return ChatMessageContentPart.CreateInputAudioPart(BinaryData.FromBytes(data), GetChatInputAudioFormat(audioContent.MimeType));
        }

        throw new ArgumentException($"{nameof(AudioContent)} must have Data bytes.");
    }

    private static ChatInputAudioFormat GetChatInputAudioFormat(string? mimeType)
    {
        if (string.IsNullOrWhiteSpace(mimeType))
        {
            return ChatInputAudioFormat.Mp3;
        }

        return mimeType.ToUpperInvariant() switch
        {
            "AUDIO/WAV" => ChatInputAudioFormat.Wav,
            "AUDIO/MP3" => ChatInputAudioFormat.Mp3,
            _ => throw new NotSupportedException($"Unsupported audio format '{mimeType}'. Supported formats are 'audio/wav' and 'audio/mp3'.")
        };
    }

    private static ChatImageDetailLevel? GetChatImageDetailLevel(ImageContent imageContent)
    {
        const string DetailLevelProperty = "ChatImageDetailLevel";

        if (imageContent.Metadata is not null &&
            imageContent.Metadata.TryGetValue(DetailLevelProperty, out object? detailLevel) &&
            detailLevel is not null)
        {
            if (detailLevel is string detailLevelString && !string.IsNullOrWhiteSpace(detailLevelString))
            {
                return detailLevelString.ToUpperInvariant() switch
                {
                    "AUTO" => ChatImageDetailLevel.Auto,
                    "LOW" => ChatImageDetailLevel.Low,
                    "HIGH" => ChatImageDetailLevel.High,
                    _ => throw new ArgumentException($"Unknown image detail level '{detailLevelString}'. Supported values are 'Auto', 'Low' and 'High'.")
                };
            }
        }

        return null;
    }

    private OpenAIChatMessageContent CreateChatMessageContent(OAIChat.ChatCompletion completion, string targetModel, bool retainArgumentTypes, OAIChat.ChatCompletionOptions options)
    {
        var message = new OpenAIChatMessageContent(completion, targetModel, this.GetChatCompletionMetadata(completion));

        if (completion.OutputAudio is ChatOutputAudio outputAudio)
        {
            var audioContent = new AudioContent(outputAudio.AudioBytes, GetAudioOutputMimeType(options.AudioOptions))
            {
                Metadata = new Dictionary<string, object?>
                {
                    [nameof(outputAudio.Id)] = outputAudio.Id,
                    [nameof(outputAudio.Transcript)] = outputAudio.Transcript,
                    [nameof(outputAudio.ExpiresAt)] = outputAudio.ExpiresAt,
                }
            };

            message.Items.Add(audioContent);
        }

        message.Items.AddRange(this.GetFunctionCallContents(completion.ToolCalls, retainArgumentTypes));

        return message;
    }

    private static string? GetAudioOutputMimeType(ChatAudioOptions? audioOptions)
    {
        if (audioOptions is null)
        {
            return null;
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Wav)
        {
            return "audio/wav";
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Mp3)
        {
            return "audio/mp3";
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Opus)
        {
            return "audio/opus";
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Wav)
        {
            return "audio/wav";
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Flac)
        {
            return "audio/flac";
        }

        if (audioOptions.OutputAudioFormat == ChatOutputAudioFormat.Pcm16)
        {
            return "audio/pcm16";
        }

        throw new NotSupportedException($"Unsupported audio output format '{audioOptions.OutputAudioFormat}'. Supported formats are 'wav', 'mp3', 'opus', 'flac' and 'pcm16'.");
    }

    private OpenAIChatMessageContent CreateChatMessageContent(ChatMessageRole chatRole, string content, ChatToolCall[] toolCalls, FunctionCallContent[]? functionCalls, IReadOnlyDictionary<string, object?>? metadata, string? authorName)
    {
        var message = new OpenAIChatMessageContent(chatRole, content, this.ModelId, toolCalls, metadata)
        {
            AuthorName = authorName,
        };

        if (functionCalls is not null)
        {
            message.Items.AddRange(functionCalls);
        }

        return message;
    }

    private List<FunctionCallContent> GetFunctionCallContents(IEnumerable<ChatToolCall> toolCalls, bool retainArgumentTypes)
    {
        List<FunctionCallContent> result = [];

        foreach (var toolCall in toolCalls)
        {
            // Adding items of 'FunctionCallContent' type to the 'Items' collection even though the function calls are available via the 'ToolCalls' property.
            // This allows consumers to work with functions in an LLM-agnostic way.
            if (toolCall.Kind == ChatToolCallKind.Function)
            {
                Exception? exception = null;
                KernelArguments? arguments = null;
                try
                {
                    arguments = JsonSerializer.Deserialize<KernelArguments>(toolCall.FunctionArguments);
                    if (arguments is { Count: > 0 } && !retainArgumentTypes)
                    {
                        // Iterate over copy of the names to avoid mutating the dictionary while enumerating it
                        var names = arguments.Names.ToArray();
                        foreach (var name in names)
                        {
                            arguments[name] = arguments[name]?.ToString();
                        }
                    }
                }
                catch (JsonException ex)
                {
                    exception = new KernelException("Error: Function call arguments were invalid JSON.", ex);

                    if (this.Logger!.IsEnabled(LogLevel.Debug))
                    {
                        this.Logger.LogDebug(ex, "Failed to deserialize function arguments ({FunctionName}/{FunctionId}).", toolCall.FunctionName, toolCall.Id);
                    }
                }

                var functionName = FunctionName.Parse(toolCall.FunctionName, OpenAIFunction.NameSeparator);

                var functionCallContent = new FunctionCallContent(
                    functionName: functionName.Name,
                    pluginName: functionName.PluginName,
                    id: toolCall.Id,
                    arguments: arguments)
                {
                    InnerContent = toolCall,
                    Exception = exception
                };

                result.Add(functionCallContent);
            }
        }

        return result;
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    /// <summary>
    /// Gets the response modalities from the execution settings.
    /// </summary>
    /// <param name="executionSettings">The execution settings.</param>
    /// <returns>The response modalities as a <see cref="ChatResponseModalities"/> flags enum.</returns>
    /// <remarks>
    /// This method supports converting from various formats:
    /// <list type="bullet">
    /// <item><description>A <see cref="ChatResponseModalities"/> flags enum</description></item>
    /// <item><description>A string representation of the enum (e.g., "Text, Audio")</description></item>
    /// <item><description>An <see cref="IEnumerable{String}"/> of modality names (e.g., ["text", "audio"])</description></item>
    /// <item><description>A <see cref="JsonElement"/> containing either a string, or array of strings</description></item>
    /// </list>
    /// </remarks>
    private static ChatResponseModalities GetResponseModalities(OpenAIPromptExecutionSettings executionSettings)
    {
        static ChatResponseModalities ParseResponseModalitiesEnumerable(IEnumerable<string> responseModalitiesStrings)
        {
            ChatResponseModalities result = ChatResponseModalities.Default;
            foreach (var modalityString in responseModalitiesStrings)
            {
                if (Enum.TryParse<ChatResponseModalities>(modalityString, true, out var parsedModality))
                {
                    result |= parsedModality;
                }
                else
                {
                    throw new NotSupportedException($"The provided response modalities '{modalityString}' is not supported.");
                }
            }

            return result;
        }

        if (executionSettings.Modalities is null)
        {
            return ChatResponseModalities.Default;
        }

        if (executionSettings.Modalities is ChatResponseModalities responseModalities)
        {
            return responseModalities;
        }

        if (executionSettings.Modalities is IEnumerable<string> responseModalitiesStrings)
        {
            return ParseResponseModalitiesEnumerable(responseModalitiesStrings);
        }

        if (executionSettings.Modalities is string responseModalitiesString)
        {
            if (Enum.TryParse<ChatResponseModalities>(responseModalitiesString, true, out var parsedResponseModalities))
            {
                return parsedResponseModalities;
            }
            throw new NotSupportedException($"The provided response modalities '{responseModalitiesString}' is not supported.");
        }

        if (executionSettings.Modalities is JsonElement responseModalitiesElement)
        {
            if (responseModalitiesElement.ValueKind == JsonValueKind.String &&
                Enum.TryParse<ChatResponseModalities>(responseModalitiesElement.GetString(), true, out var parsedResponseModalities))
            {
                return parsedResponseModalities;
            }

            if (responseModalitiesElement.ValueKind == JsonValueKind.Array)
            {
                var modalitiesEnumeration = JsonSerializer.Deserialize<IEnumerable<string>>(responseModalitiesElement.GetRawText())!;
                return ParseResponseModalitiesEnumerable(modalitiesEnumeration);
            }

            throw new NotSupportedException($"The provided response modalities '{executionSettings.Modalities?.GetType()}' is not supported.");
        }

        return ChatResponseModalities.Default;
    }

    /// <summary>
    /// Gets the audio options from the execution settings.
    /// </summary>
    /// <param name="executionSettings">The execution settings.</param>
    /// <returns>The audio options as a <see cref="ChatAudioOptions"/> object.</returns>
    /// <remarks>
    /// This method supports converting from various formats:
    /// <list type="bullet">
    /// <item><description>A <see cref="ChatAudioOptions"/> object</description></item>
    /// <item><description>A <see cref="JsonElement"/> containing the serialized audio options</description></item>
    /// <item><description>A <see cref="string"/> containing the JSON representation of the audio options</description></item>
    /// </list>
    /// </remarks>
    private static ChatAudioOptions GetAudioOptions(OpenAIPromptExecutionSettings executionSettings)
    {
        if (executionSettings.Audio is ChatAudioOptions audioOptions)
        {
            return audioOptions;
        }

        if (executionSettings.Audio is JsonElement audioOptionsElement)
        {
            var result = ModelReaderWriter.Read<ChatAudioOptions>(BinaryData.FromString(audioOptionsElement.GetRawText()));
            if (result != null)
            {
                return result;
            }
        }

        if (executionSettings.Audio is string audioOptionsString)
        {
            var result = ModelReaderWriter.Read<ChatAudioOptions>(BinaryData.FromString(audioOptionsString));
            if (result != null)
            {
                return result;
            }
        }

        throw new NotSupportedException($"The provided audio options '{executionSettings.Audio?.GetType()}' is not supported.");
    }

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    /// <param name="usage">Instance of <see cref="ChatTokenUsage"/> with token usage details.</param>
    private void LogUsage(ChatTokenUsage usage)
    {
        if (usage is null)
        {
            this.Logger!.LogDebug("Token usage information unavailable.");
            return;
        }

        if (this.Logger!.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation(
                "Prompt tokens: {InputTokenCount}. Completion tokens: {OutputTokenCount}. Total tokens: {TotalTokenCount}.",
                usage.InputTokenCount, usage.OutputTokenCount, usage.TotalTokenCount);
        }

        s_promptTokensCounter.Add(usage.InputTokenCount);
        s_completionTokensCounter.Add(usage.OutputTokenCount);
        s_totalTokensCounter.Add(usage.TotalTokenCount);
    }

    private ToolCallingConfig GetFunctionCallingConfiguration(Kernel? kernel, OpenAIPromptExecutionSettings executionSettings, ChatHistory chatHistory, int requestIndex)
    {
        // If neither behavior is specified, we just return default configuration with no tool and no choice
        if (executionSettings.FunctionChoiceBehavior is null && executionSettings.ToolCallBehavior is null)
        {
            return new ToolCallingConfig(Tools: null, Choice: null, AutoInvoke: false, AllowAnyRequestedKernelFunction: false, Options: null);
        }

        // If both behaviors are specified, we can't handle that.
        if (executionSettings.FunctionChoiceBehavior is not null && executionSettings.ToolCallBehavior is not null)
        {
            throw new ArgumentException($"{nameof(executionSettings.ToolCallBehavior)} and {nameof(executionSettings.FunctionChoiceBehavior)} cannot be used together.");
        }

        IList<ChatTool>? tools = null;
        ChatToolChoice? choice = null;
        bool autoInvoke = false;
        bool allowAnyRequestedKernelFunction = false;
        FunctionChoiceBehaviorOptions? options = null;

        // Handling new tool behavior represented by `PromptExecutionSettings.FunctionChoiceBehavior` property.
        if (executionSettings.FunctionChoiceBehavior is { } functionChoiceBehavior)
        {
            (tools, choice, autoInvoke, options) = this.ConfigureFunctionCalling(kernel, requestIndex, functionChoiceBehavior, chatHistory);
        }
        // Handling old-style tool call behavior represented by `OpenAIPromptExecutionSettings.ToolCallBehavior` property.
        else if (executionSettings.ToolCallBehavior is { } toolCallBehavior)
        {
            (tools, choice, autoInvoke, int maximumAutoInvokeAttempts, allowAnyRequestedKernelFunction) = this.ConfigureFunctionCalling(kernel, requestIndex, toolCallBehavior);

            // Disable auto invocation if we've exceeded the allowed limit.
            if (requestIndex >= maximumAutoInvokeAttempts)
            {
                autoInvoke = false;
                if (this.Logger!.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", maximumAutoInvokeAttempts);
                }
            }
            // Disable auto invocation if we've exceeded the allowed limit of in-flight auto-invokes.
            else if (FunctionCalling.FunctionCallsProcessor.s_inflightAutoInvokes.Value >= MaxInflightAutoInvokes)
            {
                autoInvoke = false;
            }
        }

        return new ToolCallingConfig(
            Tools: tools ?? [s_nonInvocableFunctionTool],
            Choice: choice ?? ChatToolChoice.CreateNoneChoice(),
            AutoInvoke: autoInvoke,
            AllowAnyRequestedKernelFunction: allowAnyRequestedKernelFunction,
            Options: options);
    }

    private (IList<ChatTool>? Tools, ChatToolChoice? Choice, bool AutoInvoke, int MaximumAutoInvokeAttempts, bool AllowAnyRequestedKernelFunction) ConfigureFunctionCalling(Kernel? kernel, int requestIndex, ToolCallBehavior toolCallBehavior)
    {
        IList<ChatTool>? tools = null;
        ChatToolChoice? choice = null;
        bool autoInvoke = kernel is not null && toolCallBehavior.MaximumAutoInvokeAttempts > 0;
        bool allowAnyRequestedKernelFunction = toolCallBehavior.AllowAnyRequestedKernelFunction;
        int maximumAutoInvokeAttempts = toolCallBehavior.MaximumAutoInvokeAttempts;

        if (requestIndex >= toolCallBehavior.MaximumUseAttempts)
        {
            // Don't add any tools as we've reached the maximum attempts limit.
            if (this.Logger!.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum use ({MaximumUse}) reached.", toolCallBehavior.MaximumUseAttempts);
            }
        }
        else
        {
            (tools, choice) = toolCallBehavior.ConfigureOptions(kernel);
        }

        return new(tools, choice, autoInvoke, maximumAutoInvokeAttempts, allowAnyRequestedKernelFunction);
    }

    private (IList<ChatTool>? Tools, ChatToolChoice? Choice, bool AutoInvoke, FunctionChoiceBehaviorOptions? Options) ConfigureFunctionCalling(Kernel? kernel, int requestIndex, FunctionChoiceBehavior functionChoiceBehavior, ChatHistory chatHistory)
    {
        FunctionChoiceBehaviorConfiguration? config = this.FunctionCallsProcessor.GetConfiguration(functionChoiceBehavior, chatHistory, requestIndex, kernel);

        IList<ChatTool>? tools = null;
        ChatToolChoice? toolChoice = null;
        bool autoInvoke = config?.AutoInvoke ?? false;

        if (config?.Functions is { Count: > 0 } functions)
        {
            if (config.Choice == FunctionChoice.Auto)
            {
                toolChoice = ChatToolChoice.CreateAutoChoice();
            }
            else if (config.Choice == FunctionChoice.Required)
            {
                toolChoice = ChatToolChoice.CreateRequiredChoice();
            }
            else if (config.Choice == FunctionChoice.None)
            {
                toolChoice = ChatToolChoice.CreateNoneChoice();
            }
            else
            {
                throw new NotSupportedException($"Unsupported function choice '{config.Choice}'.");
            }

            tools = [];

            foreach (var function in functions)
            {
                tools.Add(function.Metadata.ToOpenAIFunction().ToFunctionDefinition(config?.Options?.AllowStrictSchemaAdherence ?? false));
            }
        }

        return new(tools, toolChoice, autoInvoke, config?.Options);
    }

    /// <summary>
    /// Processes non-function tool calls.
    /// </summary>
    /// <param name="toolCalls">All tool calls requested by AI model.</param>
    /// <param name="chatHistory">The chat history.</param>
    private void ProcessNonFunctionToolCalls(IEnumerable<ChatToolCall> toolCalls, ChatHistory chatHistory)
    {
        var nonFunctionToolCalls = toolCalls.Where(toolCall => toolCall.Kind != ChatToolCallKind.Function);

        const string ErrorMessage = "Error: Tool call was not a function call.";

        foreach (var toolCall in nonFunctionToolCalls)
        {
            if (this.Logger!.IsEnabled(LogLevel.Debug))
            {
                this.Logger!.LogDebug("Failed to handle tool request ({ToolId}). {Error}", toolCall.Id, ErrorMessage);
            }

            // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
            var message = new ChatMessageContent(role: AuthorRole.Tool, content: ErrorMessage, metadata: new Dictionary<string, object?> { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } });

            chatHistory.Add(message);
        }
    }

    /// <summary>
    /// Sanitizes function names by replacing disallowed characters.
    /// </summary>
    /// <param name="toolCalls">The function calls containing the function names which need to be sanitized.</param>
    /// <returns>The function calls with sanitized function names.</returns>
    private static List<ChatToolCall> SanitizeFunctionNames(List<ChatToolCall> toolCalls)
    {
        for (int i = 0; i < toolCalls.Count; i++)
        {
            ChatToolCall tool = toolCalls[i];

            // Check if function name contains disallowed characters and replace them with '_'.
            if (DisallowedFunctionNameCharactersRegex().IsMatch(tool.FunctionName))
            {
                var sanitizedName = DisallowedFunctionNameCharactersRegex().Replace(tool.FunctionName, "_");

                toolCalls[i] = ChatToolCall.CreateFunctionToolCall(tool.Id, sanitizedName, tool.FunctionArguments);
            }
        }

        return toolCalls;
    }
}
