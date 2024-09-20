﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using JsonSchemaMapper;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using OpenAI.Chat;
using OpenAIChatCompletion = OpenAI.Chat.ChatCompletion;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// <see cref="JsonSchemaMapperConfiguration"/> for JSON schema format for structured outputs.
    /// </summary>
    private static readonly JsonSchemaMapperConfiguration s_jsonSchemaMapperConfiguration = new()
    {
        IncludeSchemaVersion = false,
        IncludeTypeInEnums = true,
        TreatNullObliviousAsNonNullable = true,
        TransformSchemaNode = OpenAIJsonSchemaTransformer.Transform
    };

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

    protected virtual Dictionary<string, object?> GetChatCompletionMetadata(OpenAIChatCompletion completions)
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
            { nameof(completionUpdate.Id), completionUpdate.Id },
            { nameof(completionUpdate.CreatedAt), completionUpdate.CreatedAt },
            { nameof(completionUpdate.SystemFingerprint), completionUpdate.SystemFingerprint },
            { nameof(completionUpdate.RefusalUpdate), completionUpdate.RefusalUpdate },

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
                JsonSerializer.Serialize(chatHistory),
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
            OpenAIChatCompletion? chatCompletion = null;
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
                            .SetPromptTokenUsage(chatCompletion.Usage.InputTokens)
                            .SetCompletionTokenUsage(chatCompletion.Usage.OutputTokens);
                    }
                    throw;
                }

                chatMessageContent = this.CreateChatMessageContent(chatCompletion, targetModel);
                activity?.SetCompletionResponse([chatMessageContent], chatCompletion.Usage.InputTokens, chatCompletion.Usage.OutputTokens);
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
                chatHistory,
                requestIndex,
                (FunctionCallContent content) => IsRequestableTool(chatOptions.Tools, content),
                kernel,
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
                JsonSerializer.Serialize(chatHistory),
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

            var toolCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, requestIndex);

            var chatOptions = this.CreateChatCompletionOptions(chatExecutionSettings, chatHistory, toolCallingConfig, kernel);

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
                        if (toolCallingConfig.AutoInvoke)
                        {
                            try
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
                            catch (NullReferenceException)
                            {
                                // Temporary workaround for OpenAI SDK Bug here: https://github.com/openai/openai-dotnet/issues/198
                                // TODO: Remove this try-catch block once the bug is fixed.
                            }
                        }

                        var openAIStreamingChatMessageContent = new OpenAIStreamingChatMessageContent(chatCompletionUpdate, 0, targetModel, metadata);

                        if (openAIStreamingChatMessageContent.ToolCallUpdates is not null)
                        {
                            foreach (var functionCallUpdate in openAIStreamingChatMessageContent.ToolCallUpdates!)
                            {
                                // Using the code below to distinguish and skip non - function call related updates.
                                // The Kind property of updates can't be reliably used because it's only initialized for the first update.
                                if (string.IsNullOrEmpty(functionCallUpdate.Id) &&
                                    string.IsNullOrEmpty(functionCallUpdate.FunctionName) &&
                                    string.IsNullOrEmpty(functionCallUpdate.FunctionArgumentsUpdate))
                                {
                                    continue;
                                }

                                openAIStreamingChatMessageContent.Items.Add(new StreamingFunctionCallUpdateContent(
                                    callId: functionCallUpdate.Id,
                                    name: functionCallUpdate.FunctionName,
                                    arguments: functionCallUpdate.FunctionArgumentsUpdate,
                                    functionCallIndex: functionCallUpdate.Index));
                            }
                        }
                        streamedContents?.Add(openAIStreamingChatMessageContent);
                        yield return openAIStreamingChatMessageContent;
                    }

                    // Translate all entries into ChatCompletionsFunctionToolCall instances.
                    toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToFunctionToolCalls(
                        ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);

                    // Translate all entries into FunctionCallContent instances for diagnostics purposes.
                    functionCallContents = this.GetFunctionCallContents(toolCalls).ToArray();
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
            if (!toolCallingConfig.AutoInvoke ||
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
                chatHistory,
                requestIndex,
                (FunctionCallContent content) => IsRequestableTool(chatOptions.Tools, content),
                kernel,
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
            MaxTokens = executionSettings.MaxTokens,
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
        };

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

        return options;
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
                        return ChatResponseFormat.JsonObject;

                    case "text":
                        return ChatResponseFormat.Text;
                }
                break;

            case JsonElement formatElement:
                // This is a workaround for a type mismatch when deserializing a JSON into an object? type property.
                // Handling only string formatElement.
                if (formatElement.ValueKind == JsonValueKind.String)
                {
                    string formatString = formatElement.GetString() ?? "";
                    switch (formatString)
                    {
                        case "json_object":
                            return ChatResponseFormat.JsonObject;

                        case "text":
                            return ChatResponseFormat.Text;
                    }
                }
                break;
            case Type formatObjectType:
                return GetJsonSchemaResponseFormat(formatObjectType);
        }

        return null;
    }

    /// <summary>
    /// Gets instance of <see cref="ChatResponseFormat"/> object for JSON schema format for structured outputs.
    /// </summary>
    private static ChatResponseFormat GetJsonSchemaResponseFormat(Type formatObjectType)
    {
        var type = formatObjectType.IsGenericType && formatObjectType.GetGenericTypeDefinition() == typeof(Nullable<>) ?
            Nullable.GetUnderlyingType(formatObjectType)! :
            formatObjectType;

        var schema = KernelJsonSchemaBuilder.Build(options: null, type, configuration: s_jsonSchemaMapperConfiguration);
        var schemaBinaryData = BinaryData.FromString(schema.ToString());

        return ChatResponseFormat.CreateJsonSchemaFormat(type.Name, schemaBinaryData, strictSchemaEnabled: true);
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
    /// <returns>Chat object</returns>
    private static ChatHistory CreateNewChat(string? text = null, OpenAIPromptExecutionSettings? executionSettings = null)
    {
        var chat = new ChatHistory();

        // If settings is not provided, create a new chat with the text as the system prompt
        AuthorRole textRole = AuthorRole.System;

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatSystemPrompt))
        {
            chat.AddSystemMessage(executionSettings!.ChatSystemPrompt!);
            textRole = AuthorRole.User;
        }

        if (!string.IsNullOrWhiteSpace(text))
        {
            chat.AddMessage(textRole, text!);
        }

        return chat;
    }

    private static List<ChatMessage> CreateChatCompletionMessages(OpenAIPromptExecutionSettings executionSettings, ChatHistory chatHistory)
    {
        List<ChatMessage> messages = [];

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

            return [new UserChatMessage(message.Items.Select(static (KernelContent item) => (ChatMessageContentPart)(item switch
            {
                TextContent textContent => ChatMessageContentPart.CreateTextMessageContentPart(textContent.Text),
                ImageContent imageContent => GetImageContentItem(imageContent),
                _ => throw new NotSupportedException($"Unsupported chat message content type '{item.GetType()}'.")
            })))
            { ParticipantName = message.AuthorName }];
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
                            ftcs.Add(ChatToolCall.CreateFunctionToolCall(id.GetString()!, name.GetString()!, arguments.GetString()!));
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

                toolCalls.Add(ChatToolCall.CreateFunctionToolCall(callRequest.Id, FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OpenAIFunction.NameSeparator), argument ?? string.Empty));
            }

            // This check is necessary to prevent an exception that will be thrown if the toolCalls collection is empty.
            // HTTP 400 (invalid_request_error:) [] should be non-empty - 'messages.3.tool_calls'  
            if (toolCalls.Count == 0)
            {
                return [new AssistantChatMessage(message.Content) { ParticipantName = message.AuthorName }];
            }

            return [new AssistantChatMessage(toolCalls, message.Content) { ParticipantName = message.AuthorName }];
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static ChatMessageContentPart GetImageContentItem(ImageContent imageContent)
    {
        if (imageContent.Data is { IsEmpty: false } data)
        {
            return ChatMessageContentPart.CreateImageMessageContentPart(BinaryData.FromBytes(data), imageContent.MimeType);
        }

        if (imageContent.Uri is not null)
        {
            return ChatMessageContentPart.CreateImageMessageContentPart(imageContent.Uri);
        }

        throw new ArgumentException($"{nameof(ImageContent)} must have either Data or a Uri.");
    }

    private OpenAIChatMessageContent CreateChatMessageContent(OpenAIChatCompletion completion, string targetModel)
    {
        var message = new OpenAIChatMessageContent(completion, targetModel, this.GetChatCompletionMetadata(completion));

        message.Items.AddRange(this.GetFunctionCallContents(completion.ToolCalls));

        return message;
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

    private List<FunctionCallContent> GetFunctionCallContents(IEnumerable<ChatToolCall> toolCalls)
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
                    if (arguments is not null)
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
                "Prompt tokens: {InputTokens}. Completion tokens: {OutputTokens}. Total tokens: {TotalTokens}.",
                usage.InputTokens, usage.OutputTokens, usage.TotalTokens);
        }

        s_promptTokensCounter.Add(usage.InputTokens);
        s_completionTokensCounter.Add(usage.OutputTokens);
        s_totalTokensCounter.Add(usage.TotalTokens);
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
            Choice: choice ?? ChatToolChoice.None,
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
                toolChoice = ChatToolChoice.Auto;
            }
            else if (config.Choice == FunctionChoice.Required)
            {
                toolChoice = ChatToolChoice.Required;
            }
            else if (config.Choice == FunctionChoice.None)
            {
                toolChoice = ChatToolChoice.None;
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
}
