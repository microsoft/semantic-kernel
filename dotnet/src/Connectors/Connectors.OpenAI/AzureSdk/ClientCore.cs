// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Contents;
using Microsoft.SemanticKernel.Http;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal abstract class ClientCore
{
    private const int MaxResultsPerPrompt = 128;

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
    private const int MaxInflightAutoInvokes = 5;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    internal ClientCore(ILogger? logger = null)
    {
        this.Logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Model Id or Deployment Name
    /// </summary>
    internal string DeploymentOrModelName { get; set; } = string.Empty;

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal abstract OpenAIClient Client { get; }

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = new();

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

    /// <summary>
    /// Creates completions for the prompt and settings.
    /// </summary>
    /// <param name="text">The prompt to complete.</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Completions generated by the remote model</returns>
    internal async Task<IReadOnlyList<TextContent>> GetTextResultsAsync(
        string text,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings textExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings, OpenAIPromptExecutionSettings.DefaultTextMaxTokens);

        ValidateMaxTokens(textExecutionSettings.MaxTokens);

        var options = CreateCompletionsOptions(text, textExecutionSettings, this.DeploymentOrModelName);

        var responseData = (await RunRequestAsync(() => this.Client.GetCompletionsAsync(options, cancellationToken)).ConfigureAwait(false)).Value;
        if (responseData.Choices.Count == 0)
        {
            throw new KernelException("Text completions not found");
        }

        this.CaptureUsageDetails(responseData.Usage);
        IReadOnlyDictionary<string, object?> metadata = GetResponseMetadata(responseData);
        return responseData.Choices.Select(choice => new TextContent(choice.Text, this.DeploymentOrModelName, choice, Encoding.UTF8, metadata)).ToList();
    }

    internal async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings textExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings, OpenAIPromptExecutionSettings.DefaultTextMaxTokens);

        ValidateMaxTokens(textExecutionSettings.MaxTokens);

        var options = CreateCompletionsOptions(prompt, textExecutionSettings, this.DeploymentOrModelName);

        StreamingResponse<Completions>? response = await RunRequestAsync(() => this.Client.GetCompletionsStreamingAsync(options, cancellationToken)).ConfigureAwait(false);

        IReadOnlyDictionary<string, object?>? metadata = null;
        await foreach (Completions completions in response)
        {
            metadata ??= GetResponseMetadata(completions);
            foreach (Choice choice in completions.Choices)
            {
                yield return new OpenAIStreamingTextContent(choice.Text, choice.Index, this.DeploymentOrModelName, choice, metadata);
            }
        }
    }

    private static Dictionary<string, object?> GetResponseMetadata(Completions completions)
    {
        return new Dictionary<string, object?>(4)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
            { nameof(completions.Usage), completions.Usage },
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(ChatCompletions completions)
    {
        return new Dictionary<string, object?>(5)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
            { nameof(completions.Usage), completions.Usage },
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(StreamingChatCompletionsUpdate completions)
    {
        return new Dictionary<string, object?>(3)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(AudioTranscription audioTranscription)
    {
        return new Dictionary<string, object?>(3)
        {
            { nameof(audioTranscription.Language), audioTranscription.Language },
            { nameof(audioTranscription.Duration), audioTranscription.Duration },
            { nameof(audioTranscription.Segments), audioTranscription.Segments }
        };
    }

    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    internal async Task<IList<ReadOnlyMemory<float>>> GetEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        CancellationToken cancellationToken)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);

        if (data.Count > 0)
        {
            var response = await RunRequestAsync(() => this.Client.GetEmbeddingsAsync(new(this.DeploymentOrModelName, data), cancellationToken)).ConfigureAwait(false);
            var embeddings = response.Value.Data;

            if (embeddings.Count != data.Count)
            {
                throw new KernelException($"Expected {data.Count} text embedding(s), but received {embeddings.Count}");
            }

            for (var i = 0; i < embeddings.Count; i++)
            {
                result.Add(embeddings[i].Embedding);
            }
        }

        return result;
    }

    internal async Task<TextContent> GetTextContentFromAudioAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(content.Data);

        OpenAIAudioToTextExecutionSettings? audioExecutionSettings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings);

        Verify.ValidFilename(audioExecutionSettings?.Filename);

        var audioOptions = new AudioTranscriptionOptions
        {
            AudioData = content.Data,
            DeploymentName = this.DeploymentOrModelName,
            Filename = audioExecutionSettings.Filename,
            Language = audioExecutionSettings.Language,
            Prompt = audioExecutionSettings.Prompt,
            ResponseFormat = audioExecutionSettings.ResponseFormat,
            Temperature = audioExecutionSettings.Temperature
        };

        AudioTranscription responseData = (await RunRequestAsync(() => this.Client.GetAudioTranscriptionAsync(audioOptions, cancellationToken)).ConfigureAwait(false)).Value;

        return new TextContent(responseData.Text, this.DeploymentOrModelName, metadata: GetResponseMetadata(responseData));
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

        // Convert the incoming execution settings to OpenAI settings.
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        bool autoInvoke = kernel is not null && chatExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0 && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;
        ValidateMaxTokens(chatExecutionSettings.MaxTokens);
        ValidateAutoInvoke(autoInvoke, chatExecutionSettings.ResultsPerPrompt);

        // Create the Azure SDK ChatCompletionOptions instance from all available information.
        var chatOptions = CreateChatCompletionsOptions(chatExecutionSettings, chat, kernel, this.DeploymentOrModelName);

        for (int iteration = 1; ; iteration++)
        {
            // Make the request.
            var responseData = (await RunRequestAsync(() => this.Client.GetChatCompletionsAsync(chatOptions, cancellationToken)).ConfigureAwait(false)).Value;
            this.CaptureUsageDetails(responseData.Usage);
            if (responseData.Choices.Count == 0)
            {
                throw new KernelException("Chat completions not found");
            }

            IReadOnlyDictionary<string, object?> metadata = GetResponseMetadata(responseData);

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!autoInvoke || responseData.Choices.Count != 1)
            {
                return responseData.Choices.Select(chatChoice => new OpenAIChatMessageContent(chatChoice.Message, this.DeploymentOrModelName, metadata)).ToList();
            }

            Debug.Assert(kernel is not null);

            // Get our single result and extract the function call information. If this isn't a function call, or if it is
            // but we're unable to find the function or extract the relevant information, just return the single result.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            ChatChoice resultChoice = responseData.Choices[0];
            OpenAIChatMessageContent result = new(resultChoice.Message, this.DeploymentOrModelName, metadata);
            if (result.ToolCalls.Count == 0)
            {
                return new[] { result };
            }

            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Tool requests: {Requests}", result.ToolCalls.Count);
            }
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", result.ToolCalls.OfType<ChatCompletionsFunctionToolCall>().Select(ftc => $"{ftc.Name}({ftc.Arguments})")));
            }

            // Add the original assistant message to the chatOptions; this is required for the service
            // to understand the tool call responses. Also add the result message to the caller's chat
            // history: if they don't want it, they can remove it, but this makes the data available,
            // including metadata like usage.
            chatOptions.Messages.Add(GetRequestMessage(resultChoice.Message));
            chat.Add(result);

            // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
            // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
            for (int i = 0; i < result.ToolCalls.Count; i++)
            {
                ChatCompletionsToolCall toolCall = result.ToolCalls[i];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (toolCall is not ChatCompletionsFunctionToolCall functionToolCall)
                {
                    AddResponseMessage(chatOptions, chat, result: null, "Error: Tool call was not a function call.", toolCall.Id, this.Logger);
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
                    AddResponseMessage(chatOptions, chat, result: null, "Error: Function call arguments were invalid JSON.", toolCall.Id, this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatOptions, chat, result: null, "Error: Function call request for a function that wasn't defined.", toolCall.Id, this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatOptions, chat, result: null, "Error: Requested function could not be found.", toolCall.Id, this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                s_inflightAutoInvokes.Value++;
                object? functionResult;
                try
                {
                    // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                    // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                    // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                    functionResult = (await function.InvokeAsync(kernel, functionArgs, cancellationToken: cancellationToken).ConfigureAwait(false)).GetValue<object>() ?? string.Empty;
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031
                {
                    AddResponseMessage(chatOptions, chat, null, $"Error: Exception while invoking function. {e.Message}", toolCall.Id, this.Logger);
                    continue;
                }
                finally
                {
                    s_inflightAutoInvokes.Value--;
                }
                AddResponseMessage(chatOptions, chat, functionResult as string ?? JsonSerializer.Serialize(functionResult), errorMessage: null, toolCall.Id, this.Logger);

                static void AddResponseMessage(ChatCompletionsOptions chatOptions, ChatHistory chat, string? result, string? errorMessage, string toolId, ILogger logger)
                {
                    // Log any error
                    if (errorMessage is not null && logger.IsEnabled(LogLevel.Debug))
                    {
                        Debug.Assert(result is null);
                        logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", toolId, errorMessage);
                    }

                    // Add the tool response message to both the chat options and to the chat history.
                    result ??= errorMessage ?? string.Empty;
                    chatOptions.Messages.Add(new ChatRequestToolMessage(result, toolId));
                    chat.AddMessage(AuthorRole.Tool, result, metadata: new Dictionary<string, object?> { { OpenAIChatMessageContent.ToolIdProperty, toolId } });
                }
            }

            // Respect the tool's maximum use attempts and maximum auto-invoke attempts.
            Debug.Assert(chatExecutionSettings.ToolCallBehavior is not null);

            if (iteration >= chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
            {
                // Set the tool choice to none. We'd also like to clear the tools, but doing so can make the service unhappy ("[] is too short - 'tools'").
                chatOptions.ToolChoice = ChatCompletionsToolChoice.None;
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
                }
            }

            if (iteration >= chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
            {
                autoInvoke = false;
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
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

        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        bool autoInvoke = kernel is not null && chatExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0 && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;
        ValidateAutoInvoke(autoInvoke, chatExecutionSettings.ResultsPerPrompt);

        var chatOptions = CreateChatCompletionsOptions(chatExecutionSettings, chat, kernel, this.DeploymentOrModelName);

        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;
        for (int iteration = 1; ; iteration++)
        {
            // Make the request.
            var response = await RunRequestAsync(() => this.Client.GetChatCompletionsStreamingAsync(chatOptions, cancellationToken)).ConfigureAwait(false);

            // Reset state
            contentBuilder?.Clear();
            toolCallIdsByIndex?.Clear();
            functionNamesByIndex?.Clear();
            functionArgumentBuildersByIndex?.Clear();

            // Stream the response.
            IReadOnlyDictionary<string, object?>? metadata = null;
            ChatRole? streamedRole = default;
            CompletionsFinishReason finishReason = default;
            await foreach (StreamingChatCompletionsUpdate update in response.ConfigureAwait(false))
            {
                metadata ??= GetResponseMetadata(update);
                streamedRole ??= update.Role;
                finishReason = update.FinishReason ?? default;

                // If we're intending to invoke function calls, we need to consume that function call information.
                if (autoInvoke)
                {
                    if (update.ContentUpdate is { Length: > 0 } contentUpdate)
                    {
                        (contentBuilder ??= new()).Append(contentUpdate);
                    }

                    OpenAIFunctionToolCall.TrackStreamingToolingUpdate(update.ToolCallUpdate, ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);
                }

                yield return new OpenAIStreamingChatMessageContent(update, update.ChoiceIndex ?? 0, this.DeploymentOrModelName, metadata);
            }

            // If we don't have a function to invoke, we're done.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            if (!autoInvoke ||
                toolCallIdsByIndex is not { Count: > 0 })
            {
                yield break;
            }

            // Get any response content that was streamed.
            string content = contentBuilder?.ToString() ?? string.Empty;

            // Translate all entries into ChatCompletionsFunctionToolCall instances.
            ChatCompletionsFunctionToolCall[] toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToChatCompletionsFunctionToolCalls(
                ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);

            // Log the requests
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", toolCalls.Select(fcr => $"{fcr.Name}({fcr.Arguments})")));
            }
            else if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Function call requests: {Requests}", toolCalls.Length);
            }

            // Add the original assistant message to the chatOptions; this is required for the service
            // to understand the tool call responses.
            chatOptions.Messages.Add(GetRequestMessage(streamedRole ?? default, content, toolCalls));
            chat.Add(new OpenAIChatMessageContent(streamedRole ?? default, content, this.DeploymentOrModelName, toolCalls, metadata));

            // Respond to each tooling request.
            foreach (ChatCompletionsFunctionToolCall toolCall in toolCalls)
            {
                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (string.IsNullOrEmpty(toolCall.Name))
                {
                    AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, result: null, "Error: Tool call was not a function call.", this.Logger);
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
                    AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, result: null, "Error: Function call arguments were invalid JSON.", this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, result: null, "Error: Function call request for a function that wasn't defined.", this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, result: null, "Error: Requested function could not be found.", this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                s_inflightAutoInvokes.Value++;
                object? functionResult;
                try
                {
                    // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                    // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                    // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                    functionResult = (await function.InvokeAsync(kernel, functionArgs, cancellationToken: cancellationToken).ConfigureAwait(false)).GetValue<object>() ?? string.Empty;
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031
                {
                    AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, result: null, $"Error: Exception while invoking function. {e.Message}", this.Logger);
                    continue;
                }
                finally
                {
                    s_inflightAutoInvokes.Value--;
                }
                AddResponseMessage(chatOptions, chat, streamedRole, toolCall, metadata, functionResult as string ?? JsonSerializer.Serialize(functionResult), errorMessage: null, this.Logger);

                static void AddResponseMessage(
                    ChatCompletionsOptions chatOptions, ChatHistory chat, ChatRole? streamedRole, ChatCompletionsToolCall tool, IReadOnlyDictionary<string, object?>? metadata,
                    string? result, string? errorMessage, ILogger logger)
                {
                    if (errorMessage is not null && logger.IsEnabled(LogLevel.Debug))
                    {
                        Debug.Assert(result is null);
                        logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", tool.Id, errorMessage);
                    }

                    // Add the tool response message to both the chat options and to the chat history.
                    result ??= errorMessage ?? string.Empty;
                    chatOptions.Messages.Add(new ChatRequestToolMessage(result, tool.Id));
                    chat.AddMessage(AuthorRole.Tool, result, metadata: new Dictionary<string, object?> { { OpenAIChatMessageContent.ToolIdProperty, tool.Id } });
                }
            }

            // Respect the tool's maximum use attempts and maximum auto-invoke attempts.
            Debug.Assert(chatExecutionSettings.ToolCallBehavior is not null);

            if (iteration >= chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
            {
                // Set the tool choice to none. We'd also like to clear the tools, but doing so can make the service unhappy ("[] is too short - 'tools'").
                chatOptions.ToolChoice = ChatCompletionsToolChoice.None;
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
                }
            }

            if (iteration >= chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
            {
                autoInvoke = false;
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
                }
            }
        }
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(ChatCompletionsOptions options, OpenAIFunctionToolCall ftc)
    {
        IList<ChatCompletionsToolDefinition> tools = options.Tools;
        for (int i = 0; i < tools.Count; i++)
        {
            if (tools[i] is ChatCompletionsFunctionToolDefinition def &&
                string.Equals(def.Name, ftc.FullyQualifiedName, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    internal async IAsyncEnumerable<StreamingTextContent> GetChatAsTextStreamingContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ChatHistory chat = CreateNewChat(prompt, chatSettings);

        await foreach (var chatUpdate in this.GetStreamingChatMessageContentsAsync(chat, executionSettings, kernel, cancellationToken))
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

    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    /// <summary>Gets options to use for an OpenAIClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>An instance of <see cref="OpenAIClientOptions"/>.</returns>
    internal static OpenAIClientOptions GetOpenAIClientOptions(HttpClient? httpClient)
    {
        OpenAIClientOptions options = new()
        {
            Diagnostics = { ApplicationId = HttpHeaderValues.UserAgent }
        };

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
        }

        return options;
    }

    /// <summary>
    /// Create a new empty chat instance
    /// </summary>
    /// <param name="text">Optional chat instructions for the AI service</param>
    /// <param name="executionSettings">Execution settings</param>
    /// <returns>Chat object</returns>
    internal static ChatHistory CreateNewChat(string? text = null, OpenAIPromptExecutionSettings? executionSettings = null)
    {
        var chat = new ChatHistory();

        // If settings is not provided, create a new chat with the text as the system prompt
        AuthorRole textRole = AuthorRole.System;

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatSystemPrompt))
        {
            chat.AddSystemMessage(executionSettings!.ChatSystemPrompt);
            textRole = AuthorRole.User;
        }

        if (!string.IsNullOrWhiteSpace(text))
        {
            chat.AddMessage(textRole, text!);
        }

        return chat;
    }

    private static CompletionsOptions CreateCompletionsOptions(string text, OpenAIPromptExecutionSettings executionSettings, string deploymentOrModelName)
    {
        if (executionSettings.ResultsPerPrompt is < 1 or > MaxResultsPerPrompt)
        {
            throw new ArgumentOutOfRangeException($"{nameof(executionSettings)}.{nameof(executionSettings.ResultsPerPrompt)}", executionSettings.ResultsPerPrompt, $"The value must be in range between 1 and {MaxResultsPerPrompt}, inclusive.");
        }

        var options = new CompletionsOptions
        {
            Prompts = { text.Replace("\r\n", "\n") }, // normalize line endings
            MaxTokens = executionSettings.MaxTokens,
            Temperature = (float?)executionSettings.Temperature,
            NucleusSamplingFactor = (float?)executionSettings.TopP,
            FrequencyPenalty = (float?)executionSettings.FrequencyPenalty,
            PresencePenalty = (float?)executionSettings.PresencePenalty,
            Echo = false,
            ChoicesPerPrompt = executionSettings.ResultsPerPrompt,
            GenerationSampleCount = executionSettings.ResultsPerPrompt,
            LogProbabilityCount = null,
            User = executionSettings.User,
            DeploymentName = deploymentOrModelName
        };

        if (executionSettings.TokenSelectionBiases is not null)
        {
            foreach (var keyValue in executionSettings.TokenSelectionBiases)
            {
                options.TokenSelectionBiases.Add(keyValue.Key, keyValue.Value);
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

    private static ChatCompletionsOptions CreateChatCompletionsOptions(
        OpenAIPromptExecutionSettings executionSettings,
        ChatHistory chatHistory,
        Kernel? kernel,
        string deploymentOrModelName)
    {
        if (executionSettings.ResultsPerPrompt is < 1 or > MaxResultsPerPrompt)
        {
            throw new ArgumentOutOfRangeException($"{nameof(executionSettings)}.{nameof(executionSettings.ResultsPerPrompt)}", executionSettings.ResultsPerPrompt, $"The value must be in range between 1 and {MaxResultsPerPrompt}, inclusive.");
        }

        var options = new ChatCompletionsOptions
        {
            MaxTokens = executionSettings.MaxTokens,
            Temperature = (float?)executionSettings.Temperature,
            NucleusSamplingFactor = (float?)executionSettings.TopP,
            FrequencyPenalty = (float?)executionSettings.FrequencyPenalty,
            PresencePenalty = (float?)executionSettings.PresencePenalty,
            ChoiceCount = executionSettings.ResultsPerPrompt,
            DeploymentName = deploymentOrModelName,
            Seed = executionSettings.Seed,
            User = executionSettings.User
        };

        switch (executionSettings.ResponseFormat)
        {
            case ChatCompletionsResponseFormat formatObject:
                // If the response format is an Azure SDK ChatCompletionsResponseFormat, just pass it along.
                options.ResponseFormat = formatObject;
                break;

            case string formatString:
                // If the response format is a string, map the ones we know about, and ignore the rest.
                switch (formatString)
                {
                    case "json_object":
                        options.ResponseFormat = ChatCompletionsResponseFormat.JsonObject;
                        break;

                    case "text":
                        options.ResponseFormat = ChatCompletionsResponseFormat.Text;
                        break;
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
                            options.ResponseFormat = ChatCompletionsResponseFormat.JsonObject;
                            break;

                        case "text":
                            options.ResponseFormat = ChatCompletionsResponseFormat.Text;
                            break;
                    }
                }
                break;
        }

        executionSettings.ToolCallBehavior?.ConfigureOptions(kernel, options);
        if (executionSettings.TokenSelectionBiases is not null)
        {
            foreach (var keyValue in executionSettings.TokenSelectionBiases)
            {
                options.TokenSelectionBiases.Add(keyValue.Key, keyValue.Value);
            }
        }

        if (executionSettings.StopSequences is { Count: > 0 })
        {
            foreach (var s in executionSettings.StopSequences)
            {
                options.StopSequences.Add(s);
            }
        }

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            options.Messages.Add(GetRequestMessage(new ChatMessageContent(AuthorRole.System, executionSettings!.ChatSystemPrompt)));
        }

        foreach (var message in chatHistory)
        {
            options.Messages.Add(GetRequestMessage(message));
        }

        return options;
    }

    private static ChatRequestMessage GetRequestMessage(ChatRole chatRole, string contents, ChatCompletionsFunctionToolCall[]? tools)
    {
        if (chatRole == ChatRole.User)
        {
            return new ChatRequestUserMessage(contents);
        }

        if (chatRole == ChatRole.System)
        {
            return new ChatRequestSystemMessage(contents);
        }

        if (chatRole == ChatRole.Assistant)
        {
            var msg = new ChatRequestAssistantMessage(contents);
            if (tools is not null)
            {
                foreach (ChatCompletionsFunctionToolCall tool in tools)
                {
                    msg.ToolCalls.Add(tool);
                }
            }
            return msg;
        }

        throw new NotImplementedException($"Role {chatRole} is not implemented");
    }

    private static ChatRequestMessage GetRequestMessage(ChatMessageContent message)
    {
        if (message.Role == AuthorRole.System)
        {
            return new ChatRequestSystemMessage(message.Content);
        }

        if (message.Role == AuthorRole.User || message.Role == AuthorRole.Tool)
        {
            if (message.Metadata?.TryGetValue(OpenAIChatMessageContent.ToolIdProperty, out object? toolId) is true &&
                toolId?.ToString() is string toolIdString)
            {
                return new ChatRequestToolMessage(message.Content, toolIdString);
            }

            if (message.Items is { Count: > 0 })
            {
                return new ChatRequestUserMessage(message.Items.Select(static (KernelContent item) => (ChatMessageContentItem)(item switch
                {
                    TextContent textContent => new ChatMessageTextContentItem(textContent.Text),
                    ImageContent imageContent => new ChatMessageImageContentItem(imageContent.Uri),
                    _ => throw new NotSupportedException($"Unsupported chat message content type '{item.GetType()}'.")
                })));
            }

            return new ChatRequestUserMessage(message.Content);
        }

        if (message.Role == AuthorRole.Assistant)
        {
            var asstMessage = new ChatRequestAssistantMessage(message.Content);

            IEnumerable<ChatCompletionsToolCall>? tools = (message as OpenAIChatMessageContent)?.ToolCalls;
            if (tools is null && message.Metadata?.TryGetValue(OpenAIChatMessageContent.FunctionToolCallsProperty, out object? toolCallsObject) is true)
            {
                tools = toolCallsObject as IEnumerable<ChatCompletionsFunctionToolCall>;
                if (tools is null && toolCallsObject is JsonElement { ValueKind: JsonValueKind.Array } array)
                {
                    int length = array.GetArrayLength();
                    var ftcs = new List<ChatCompletionsToolCall>(length);
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
                            ftcs.Add(new ChatCompletionsFunctionToolCall(id.GetString()!, name.GetString()!, arguments.GetString()!));
                        }
                    }
                    tools = ftcs;
                }
            }

            if (tools is not null)
            {
                foreach (ChatCompletionsToolCall tool in tools)
                {
                    asstMessage.ToolCalls.Add(tool);
                }
            }

            return asstMessage;
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static ChatRequestMessage GetRequestMessage(ChatResponseMessage message)
    {
        if (message.Role == ChatRole.System)
        {
            return new ChatRequestSystemMessage(message.Content);
        }

        if (message.Role == ChatRole.Assistant)
        {
            var msg = new ChatRequestAssistantMessage(message.Content);
            if (message.ToolCalls is { Count: > 0 } tools)
            {
                foreach (ChatCompletionsToolCall tool in tools)
                {
                    msg.ToolCalls.Add(tool);
                }
            }

            return msg;
        }

        if (message.Role == ChatRole.User)
        {
            return new ChatRequestUserMessage(message.Content);
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private static void ValidateAutoInvoke(bool autoInvoke, int resultsPerPrompt)
    {
        if (autoInvoke && resultsPerPrompt != 1)
        {
            // We can remove this restriction in the future if valuable. However, multiple results per prompt is rare,
            // and limiting this significantly curtails the complexity of the implementation.
            throw new ArgumentException($"Auto-invocation of tool calls may only be used with a {nameof(OpenAIPromptExecutionSettings.ResultsPerPrompt)} of 1.");
        }
    }

    private static async Task<T> RunRequestAsync<T>(Func<Task<T>> request)
    {
        try
        {
            return await request.Invoke().ConfigureAwait(false);
        }
        catch (RequestFailedException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    /// <param name="usage">Instance of <see cref="CompletionsUsage"/> with usage details.</param>
    private void CaptureUsageDetails(CompletionsUsage usage)
    {
        if (usage is null)
        {
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Usage information is not available.");
            }

            return;
        }

        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation(
                "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}.",
                usage.PromptTokens, usage.CompletionTokens, usage.TotalTokens);
        }

        s_promptTokensCounter.Add(usage.PromptTokens);
        s_completionTokensCounter.Add(usage.CompletionTokens);
        s_totalTokensCounter.Add(usage.TotalTokens);
    }
}
