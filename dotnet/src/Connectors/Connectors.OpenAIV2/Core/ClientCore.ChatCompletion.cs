// Copyright (c) Microsoft. All rights reserved.

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
    private const string ModelProvider = "openai";
    private record ToolCallingConfig(IList<ChatTool>? Tools, ChatToolChoice Choice, bool AutoInvoke);

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
    private const int MaxInflightAutoInvokes = 128;

    /// <summary>Singleton tool used when tool call count drops to 0 but we need to supply tools to keep the service happy.</summary>
    private static readonly ChatTool s_nonInvocableFunctionTool = ChatTool.CreateFunctionTool("NonInvocableTool");

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel.Connectors.OpenAI");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    private static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    private static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    private static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.openai.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    private static Dictionary<string, object?> GetChatCompletionMetadata(OpenAIChatCompletion completions)
    {
        return new Dictionary<string, object?>
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.CreatedAt), completions.CreatedAt },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
            { nameof(completions.Usage), completions.Usage },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completions.FinishReason), completions.FinishReason.ToString() },
            { nameof(completions.ContentTokenLogProbabilities), completions.ContentTokenLogProbabilities },
        };
    }

    private static Dictionary<string, object?> GetChatCompletionMetadata(StreamingChatCompletionUpdate completionUpdate)
    {
        return new Dictionary<string, object?>
        {
            { nameof(completionUpdate.Id), completionUpdate.Id },
            { nameof(completionUpdate.CreatedAt), completionUpdate.CreatedAt },
            { nameof(completionUpdate.SystemFingerprint), completionUpdate.SystemFingerprint },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completionUpdate.FinishReason), completionUpdate.FinishReason?.ToString() },
        };
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chat">Chat history</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Generated chat message in string format</returns>
    internal async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chat),
                JsonSerializer.Serialize(executionSettings));
        }

        // Convert the incoming execution settings to OpenAI settings.
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chat);

        for (int requestIndex = 0; ; requestIndex++)
        {
            var toolCallingConfig = this.GetToolCallingConfiguration(kernel, chatExecutionSettings, requestIndex);

            var chatOptions = this.CreateChatCompletionOptions(chatExecutionSettings, chat, toolCallingConfig, kernel);

            // Make the request.
            OpenAIChatCompletion? chatCompletion = null;
            OpenAIChatMessageContent chatMessageContent;
            using (var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.ModelId, ModelProvider, chat, chatExecutionSettings))
            {
                try
                {
                    chatCompletion = (await RunRequestAsync(() => this.Client.GetChatClient(this.ModelId).CompleteChatAsync(chatForRequest, chatOptions, cancellationToken)).ConfigureAwait(false)).Value;

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

                chatMessageContent = this.CreateChatMessageContent(chatCompletion);
                activity?.SetCompletionResponse([chatMessageContent], chatCompletion.Usage.InputTokens, chatCompletion.Usage.OutputTokens);
            }

            // If we don't want to attempt to invoke any functions, just return the result.
            if (!toolCallingConfig.AutoInvoke)
            {
                return [chatMessageContent];
            }

            Debug.Assert(kernel is not null);

            // Get our single result and extract the function call information. If this isn't a function call, or if it is
            // but we're unable to find the function or extract the relevant information, just return the single result.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            if (chatCompletion.ToolCalls.Count == 0)
            {
                return [chatMessageContent];
            }

            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Tool requests: {Requests}", chatCompletion.ToolCalls.Count);
            }
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", chatCompletion.ToolCalls.OfType<ChatToolCall>().Select(ftc => $"{ftc.FunctionName}({ftc.FunctionArguments})")));
            }

            // Add the original assistant message to the chat messages; this is required for the service
            // to understand the tool call responses. Also add the result message to the caller's chat
            // history: if they don't want it, they can remove it, but this makes the data available,
            // including metadata like usage.
            chatForRequest.Add(CreateRequestMessage(chatCompletion));
            chat.Add(chatMessageContent);

            // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
            // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
            for (int toolCallIndex = 0; toolCallIndex < chatMessageContent.ToolCalls.Count; toolCallIndex++)
            {
                ChatToolCall functionToolCall = chatMessageContent.ToolCalls[toolCallIndex];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (functionToolCall.Kind != ChatToolCallKind.Function)
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Tool call was not a function call.", functionToolCall, this.Logger);
                    continue;
                }

                // Parse the function call arguments.
                OpenAIFunctionToolCall? openAIFunctionToolCall;
                try
                {
                    openAIFunctionToolCall = new(functionToolCall);
                }
                catch (JsonException)
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Function call arguments were invalid JSON.", functionToolCall, this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Function call request for a function that wasn't defined.", functionToolCall, this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Requested function could not be found.", functionToolCall, this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                FunctionResult functionResult = new(function) { Culture = kernel.Culture };
                AutoFunctionInvocationContext invocationContext = new(kernel, function, functionResult, chat)
                {
                    Arguments = functionArgs,
                    RequestSequenceIndex = requestIndex,
                    FunctionSequenceIndex = toolCallIndex,
                    FunctionCount = chatMessageContent.ToolCalls.Count
                };

                s_inflightAutoInvokes.Value++;
                try
                {
                    invocationContext = await OnAutoFunctionInvocationAsync(kernel, invocationContext, async (context) =>
                    {
                        // Check if filter requested termination.
                        if (context.Terminate)
                        {
                            return;
                        }

                        // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                        // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                        // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                        context.Result = await function.InvokeAsync(kernel, invocationContext.Arguments, cancellationToken: cancellationToken).ConfigureAwait(false);
                    }).ConfigureAwait(false);
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031 // Do not catch general exception types
                {
                    AddResponseMessage(chatForRequest, chat, null, $"Error: Exception while invoking function. {e.Message}", functionToolCall, this.Logger);
                    continue;
                }
                finally
                {
                    s_inflightAutoInvokes.Value--;
                }

                // Apply any changes from the auto function invocation filters context to final result.
                functionResult = invocationContext.Result;

                object functionResultValue = functionResult.GetValue<object>() ?? string.Empty;
                var stringResult = ProcessFunctionResult(functionResultValue, chatExecutionSettings.ToolCallBehavior);

                AddResponseMessage(chatForRequest, chat, stringResult, errorMessage: null, functionToolCall, this.Logger);

                // If filter requested termination, returning latest function result.
                if (invocationContext.Terminate)
                {
                    if (this.Logger.IsEnabled(LogLevel.Debug))
                    {
                        this.Logger.LogDebug("Filter requested termination of automatic function invocation.");
                    }

                    return [chat.Last()];
                }
            }
        }
    }

    internal async IAsyncEnumerable<OpenAIStreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chat),
                JsonSerializer.Serialize(executionSettings));
        }

        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;

        var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chat);

        for (int requestIndex = 0; ; requestIndex++)
        {
            var toolCallingConfig = this.GetToolCallingConfiguration(kernel, chatExecutionSettings, requestIndex);

            var chatOptions = this.CreateChatCompletionOptions(chatExecutionSettings, chat, toolCallingConfig, kernel);

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

            using (var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.ModelId, ModelProvider, chat, chatExecutionSettings))
            {
                // Make the request.
                AsyncResultCollection<StreamingChatCompletionUpdate> response;
                try
                {
                    response = RunRequest(() => this.Client.GetChatClient(this.ModelId).CompleteChatStreamingAsync(chatForRequest, chatOptions, cancellationToken));
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
                            foreach (var contentPart in chatCompletionUpdate.ContentUpdate)
                            {
                                if (contentPart.Kind == ChatMessageContentPartKind.Text)
                                {
                                    (contentBuilder ??= new()).Append(contentPart.Text);
                                }
                            }

                            OpenAIFunctionToolCall.TrackStreamingToolingUpdate(chatCompletionUpdate.ToolCallUpdates, ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);
                        }

                        var openAIStreamingChatMessageContent = new OpenAIStreamingChatMessageContent(chatCompletionUpdate, 0, this.ModelId, metadata);

                        foreach (var functionCallUpdate in chatCompletionUpdate.ToolCallUpdates)
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

            // Log the requests
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", toolCalls.Select(fcr => $"{fcr.FunctionName}({fcr.FunctionName})")));
            }
            else if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Function call requests: {Requests}", toolCalls.Length);
            }

            // Add the original assistant message to the chat messages; this is required for the service
            // to understand the tool call responses.
            chatForRequest.Add(CreateRequestMessage(streamedRole ?? default, content, streamedName, toolCalls));
            chat.Add(this.CreateChatMessageContent(streamedRole ?? default, content, toolCalls, functionCallContents, metadata, streamedName));

            // Respond to each tooling request.
            for (int toolCallIndex = 0; toolCallIndex < toolCalls.Length; toolCallIndex++)
            {
                ChatToolCall toolCall = toolCalls[toolCallIndex];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (string.IsNullOrEmpty(toolCall.FunctionName))
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Tool call was not a function call.", toolCall, this.Logger);
                    continue;
                }

                // Parse the function call arguments.
                OpenAIFunctionToolCall? openAIFunctionToolCall;
                try
                {
                    openAIFunctionToolCall = new(toolCall);
                }
                catch (JsonException)
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Function call arguments were invalid JSON.", toolCall, this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Function call request for a function that wasn't defined.", toolCall, this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatForRequest, chat, result: null, "Error: Requested function could not be found.", toolCall, this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                FunctionResult functionResult = new(function) { Culture = kernel.Culture };
                AutoFunctionInvocationContext invocationContext = new(kernel, function, functionResult, chat)
                {
                    Arguments = functionArgs,
                    RequestSequenceIndex = requestIndex,
                    FunctionSequenceIndex = toolCallIndex,
                    FunctionCount = toolCalls.Length
                };

                s_inflightAutoInvokes.Value++;
                try
                {
                    invocationContext = await OnAutoFunctionInvocationAsync(kernel, invocationContext, async (context) =>
                    {
                        // Check if filter requested termination.
                        if (context.Terminate)
                        {
                            return;
                        }

                        // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                        // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                        // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                        context.Result = await function.InvokeAsync(kernel, invocationContext.Arguments, cancellationToken: cancellationToken).ConfigureAwait(false);
                    }).ConfigureAwait(false);
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031 // Do not catch general exception types
                {
                    AddResponseMessage(chatForRequest, chat, result: null, $"Error: Exception while invoking function. {e.Message}", toolCall, this.Logger);
                    continue;
                }
                finally
                {
                    s_inflightAutoInvokes.Value--;
                }

                // Apply any changes from the auto function invocation filters context to final result.
                functionResult = invocationContext.Result;

                object functionResultValue = functionResult.GetValue<object>() ?? string.Empty;
                var stringResult = ProcessFunctionResult(functionResultValue, chatExecutionSettings.ToolCallBehavior);

                AddResponseMessage(chatForRequest, chat, stringResult, errorMessage: null, toolCall, this.Logger);

                // If filter requested termination, returning latest function result and breaking request iteration loop.
                if (invocationContext.Terminate)
                {
                    if (this.Logger.IsEnabled(LogLevel.Debug))
                    {
                        this.Logger.LogDebug("Filter requested termination of automatic function invocation.");
                    }

                    var lastChatMessage = chat.Last();

                    yield return new OpenAIStreamingChatMessageContent(lastChatMessage.Role, lastChatMessage.Content);
                    yield break;
                }
            }
        }
    }

    internal async IAsyncEnumerable<StreamingTextContent> GetChatAsTextStreamingContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ChatHistory chat = CreateNewChat(prompt, chatSettings);

        await foreach (var chatUpdate in this.GetStreamingChatMessageContentsAsync(chat, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(chatUpdate.Content, chatUpdate.ChoiceIndex, chatUpdate.ModelId, chatUpdate, Encoding.UTF8, chatUpdate.Metadata);
        }
    }

    internal async Task<IReadOnlyList<TextContent>> GetChatAsTextContentsAsync(
        string text,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        ChatHistory chat = CreateNewChat(text, chatSettings);
        return (await this.GetChatMessageContentsAsync(chat, chatSettings, kernel, cancellationToken).ConfigureAwait(false))
            .Select(chat => new TextContent(chat.Content, chat.ModelId, chat.Content, Encoding.UTF8, chat.Metadata))
            .ToList();
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(ChatCompletionOptions options, OpenAIFunctionToolCall ftc)
    {
        IList<ChatTool> tools = options.Tools;
        for (int i = 0; i < tools.Count; i++)
        {
            if (tools[i].Kind == ChatToolKind.Function &&
                string.Equals(tools[i].FunctionName, ftc.FullyQualifiedName, StringComparison.OrdinalIgnoreCase))
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

    private ChatCompletionOptions CreateChatCompletionOptions(
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
            Seed = executionSettings.Seed,
            User = executionSettings.User,
            TopLogProbabilityCount = executionSettings.TopLogprobs,
            IncludeLogProbabilities = executionSettings.Logprobs,
            ResponseFormat = GetResponseFormat(executionSettings) ?? ChatResponseFormat.Text,
            ToolChoice = toolCallingConfig.Choice,
        };

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

    private static List<ChatMessage> CreateChatCompletionMessages(OpenAIPromptExecutionSettings executionSettings, ChatHistory chatHistory)
    {
        List<ChatMessage> messages = [];

        if (!string.IsNullOrWhiteSpace(executionSettings.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            messages.Add(new SystemChatMessage(executionSettings.ChatSystemPrompt));
        }

        foreach (var message in chatHistory)
        {
            messages.AddRange(CreateRequestMessages(message, executionSettings.ToolCallBehavior));
        }

        return messages;
    }

    private static ChatMessage CreateRequestMessage(ChatMessageRole chatRole, string content, string? name, ChatToolCall[]? tools)
    {
        if (chatRole == ChatMessageRole.User)
        {
            return new UserChatMessage(content) { ParticipantName = name };
        }

        if (chatRole == ChatMessageRole.System)
        {
            return new SystemChatMessage(content) { ParticipantName = name };
        }

        if (chatRole == ChatMessageRole.Assistant)
        {
            return new AssistantChatMessage(tools, content) { ParticipantName = name };
        }

        throw new NotImplementedException($"Role {chatRole} is not implemented");
    }

    private static List<ChatMessage> CreateRequestMessages(ChatMessageContent message, ToolCallBehavior? toolCallBehavior)
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

                var stringResult = ProcessFunctionResult(resultContent.Result ?? string.Empty, toolCallBehavior);

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

    private static ChatMessage CreateRequestMessage(OpenAIChatCompletion completion)
    {
        if (completion.Role == ChatMessageRole.System)
        {
            return ChatMessage.CreateSystemMessage(completion.Content[0].Text);
        }

        if (completion.Role == ChatMessageRole.Assistant)
        {
            return ChatMessage.CreateAssistantMessage(completion);
        }

        if (completion.Role == ChatMessageRole.User)
        {
            return ChatMessage.CreateUserMessage(completion.Content);
        }

        throw new NotSupportedException($"Role {completion.Role} is not supported.");
    }

    private OpenAIChatMessageContent CreateChatMessageContent(OpenAIChatCompletion completion)
    {
        var message = new OpenAIChatMessageContent(completion, this.ModelId, GetChatCompletionMetadata(completion));

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

                    if (this.Logger.IsEnabled(LogLevel.Debug))
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

    private static void AddResponseMessage(List<ChatMessage> chatMessages, ChatHistory chat, string? result, string? errorMessage, ChatToolCall toolCall, ILogger logger)
    {
        // Log any error
        if (errorMessage is not null && logger.IsEnabled(LogLevel.Debug))
        {
            Debug.Assert(result is null);
            logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", toolCall.Id, errorMessage);
        }

        // Add the tool response message to the chat messages
        result ??= errorMessage ?? string.Empty;
        chatMessages.Add(new ToolChatMessage(toolCall.Id, result));

        // Add the tool response message to the chat history.
        var message = new ChatMessageContent(role: AuthorRole.Tool, content: result, metadata: new Dictionary<string, object?> { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } });

        if (toolCall.Kind == ChatToolCallKind.Function)
        {
            // Add an item of type FunctionResultContent to the ChatMessageContent.Items collection in addition to the function result stored as a string in the ChatMessageContent.Content property.  
            // This will enable migration to the new function calling model and facilitate the deprecation of the current one in the future.
            var functionName = FunctionName.Parse(toolCall.FunctionName, OpenAIFunction.NameSeparator);
            message.Items.Add(new FunctionResultContent(functionName.Name, functionName.PluginName, toolCall.Id, result));
        }

        chat.Add(message);
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
            this.Logger.LogDebug("Token usage information unavailable.");
            return;
        }

        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation(
                "Prompt tokens: {InputTokens}. Completion tokens: {OutputTokens}. Total tokens: {TotalTokens}.",
                usage.InputTokens, usage.OutputTokens, usage.TotalTokens);
        }

        s_promptTokensCounter.Add(usage.InputTokens);
        s_completionTokensCounter.Add(usage.OutputTokens);
        s_totalTokensCounter.Add(usage.TotalTokens);
    }

    /// <summary>
    /// Processes the function result.
    /// </summary>
    /// <param name="functionResult">The result of the function call.</param>
    /// <param name="toolCallBehavior">The ToolCallBehavior object containing optional settings like JsonSerializerOptions.TypeInfoResolver.</param>
    /// <returns>A string representation of the function result.</returns>
    private static string? ProcessFunctionResult(object functionResult, ToolCallBehavior? toolCallBehavior)
    {
        if (functionResult is string stringResult)
        {
            return stringResult;
        }

        // This is an optimization to use ChatMessageContent content directly  
        // without unnecessary serialization of the whole message content class.  
        if (functionResult is ChatMessageContent chatMessageContent)
        {
            return chatMessageContent.ToString();
        }

        // For polymorphic serialization of unknown in advance child classes of the KernelContent class,  
        // a corresponding JsonTypeInfoResolver should be provided via the JsonSerializerOptions.TypeInfoResolver property.  
        // For more details about the polymorphic serialization, see the article at:  
        // https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0
#pragma warning disable CS0618 // Type or member is obsolete
        return JsonSerializer.Serialize(functionResult, toolCallBehavior?.ToolCallResultSerializerOptions);
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <summary>
    /// Executes auto function invocation filters and/or function itself.
    /// This method can be moved to <see cref="Kernel"/> when auto function invocation logic will be extracted to common place.
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

    private ToolCallingConfig GetToolCallingConfiguration(Kernel? kernel, OpenAIPromptExecutionSettings executionSettings, int requestIndex)
    {
        if (executionSettings.ToolCallBehavior is null)
        {
            return new ToolCallingConfig(Tools: [s_nonInvocableFunctionTool], Choice: ChatToolChoice.None, AutoInvoke: false);
        }

        if (requestIndex >= executionSettings.ToolCallBehavior.MaximumUseAttempts)
        {
            // Don't add any tools as we've reached the maximum attempts limit.
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", executionSettings.ToolCallBehavior!.MaximumUseAttempts);
            }

            return new ToolCallingConfig(Tools: [s_nonInvocableFunctionTool], Choice: ChatToolChoice.None, AutoInvoke: false);
        }

        var (tools, choice) = executionSettings.ToolCallBehavior.ConfigureOptions(kernel);

        bool autoInvoke = kernel is not null &&
            executionSettings.ToolCallBehavior.MaximumAutoInvokeAttempts > 0 &&
            s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;

        // Disable auto invocation if we've exceeded the allowed limit.
        if (requestIndex >= executionSettings.ToolCallBehavior.MaximumAutoInvokeAttempts)
        {
            autoInvoke = false;
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", executionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
            }
        }

        return new ToolCallingConfig(
            Tools: tools ?? [s_nonInvocableFunctionTool],
            Choice: choice ?? ChatToolChoice.None,
            AutoInvoke: autoInvoke);
    }

    private static ChatResponseFormat? GetResponseFormat(OpenAIPromptExecutionSettings executionSettings)
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
        }

        return null;
    }
}
