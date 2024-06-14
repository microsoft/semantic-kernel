// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;
using OpenAI;
using OpenAI.Audio;
using OpenAI.Chat;
using OpenAI.Embeddings;

using OpenAIChatCompletion = OpenAI.Chat.ChatCompletion;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal abstract class ClientCore
{
    private const string ModelProvider = "openai";
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
    private const int MaxInflightAutoInvokes = 128;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>Singleton tool used when tool call count drops to 0 but we need to supply tools to keep the service happy.</summary>
    private static readonly ChatTool s_nonInvocableFunctionTool = ChatTool.CreateFunctionTool("NonInvocableTool");

    internal ClientCore(ILogger? logger = null)
    {
        this.Logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Model Id or Deployment Name
    /// </summary>
    internal string ModelName { get; set; } = string.Empty;

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal abstract OpenAIClient Client { get; }

    internal Uri? Endpoint { get; set; } = null;

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

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
    /// <param name="prompt">The prompt to complete.</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Completions generated by the remote model</returns>
    internal Task<IReadOnlyList<TextContent>> GetTextResultsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        /*
        OpenAIPromptExecutionSettings textExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings, OpenAIPromptExecutionSettings.DefaultTextMaxTokens);

        ValidateMaxTokens(textExecutionSettings.MaxTokens);

        var options = CreateCompletionsOptions(prompt, textExecutionSettings, this.DeploymentOrModelName);
        Completions? responseData = null;
        List<TextContent> responseContent;
        using (var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.DeploymentOrModelName, ModelProvider, prompt, textExecutionSettings))
        {
            try
            {
                responseData = (await RunRequestAsync(() => this.Client.GetChatClient().CompleteChatAsync().GetCompletionsAsync(options, cancellationToken)).ConfigureAwait(false)).Value;
                if (responseData.Choices.Count == 0)
                {
                    throw new KernelException("Text completions not found");
                }
            }
            catch (Exception ex) when (activity is not null)
            {
                activity.SetError(ex);
                if (responseData != null)
                {
                    // Capture available metadata even if the operation failed.
                    activity
                        .SetResponseId(responseData.Id)
                        .SetPromptTokenUsage(responseData.Usage.PromptTokens)
                        .SetCompletionTokenUsage(responseData.Usage.CompletionTokens);
                }
                throw;
            }

            responseContent = responseData.Choices.Select(choice => new TextContent(choice.Text, this.DeploymentOrModelName, choice, Encoding.UTF8, GetTextChoiceMetadata(responseData, choice))).ToList();
            activity?.SetCompletionResponse(responseContent, responseData.Usage.PromptTokens, responseData.Usage.CompletionTokens);
        }

        this.LogUsage(responseData.Usage);

        return responseContent;

        */

        throw new NotSupportedException();
    }

    internal IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        /*
        OpenAIPromptExecutionSettings textExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings, OpenAIPromptExecutionSettings.DefaultTextMaxTokens);

        ValidateMaxTokens(textExecutionSettings.MaxTokens);

        var options = CreateCompletionsOptions(prompt, textExecutionSettings, this.DeploymentOrModelName);

        using var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.DeploymentOrModelName, ModelProvider, prompt, textExecutionSettings);

        StreamingResponse<Completions> response;
        try
        {
            response = await RunRequestAsync(() => this.Client.GetCompletionsStreamingAsync(options, cancellationToken)).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        var responseEnumerator = response.ConfigureAwait(false).GetAsyncEnumerator();
        List<OpenAIStreamingTextContent>? streamedContents = activity is not null ? [] : null;
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

                Completions completions = responseEnumerator.Current;
                foreach (Choice choice in completions.Choices)
                {
                    var openAIStreamingTextContent = new OpenAIStreamingTextContent(
                        choice.Text, choice.Index, this.DeploymentOrModelName, choice, GetTextChoiceMetadata(completions, choice));
                    streamedContents?.Add(openAIStreamingTextContent);
                    yield return openAIStreamingTextContent;
                }
            }
        }
        finally
        {
            activity?.EndStreaming(streamedContents);
            await responseEnumerator.DisposeAsync();
        }*/

        throw new NotSupportedException();
    }

    /*
    private static Dictionary<string, object?> GetTextChoiceMetadata(Completions completions, Choice choice)
    {
        return new Dictionary<string, object?>(8)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
            { nameof(completions.Usage), completions.Usage },
            { nameof(choice.ContentFilterResults), choice.ContentFilterResults },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(choice.FinishReason), choice.FinishReason?.ToString() },

            { nameof(choice.LogProbabilityModel), choice.LogProbabilityModel },
            { nameof(choice.Index), choice.Index },
        };
    }

    private static Dictionary<string, object?> GetChatChoiceMetadata(ChatCompletions completions, ChatChoice chatChoice)
    {
        return new Dictionary<string, object?>(12)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
            { nameof(completions.Usage), completions.Usage },
            { nameof(chatChoice.ContentFilterResults), chatChoice.ContentFilterResults },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(chatChoice.FinishReason), chatChoice.FinishReason?.ToString() },

            { nameof(chatChoice.FinishDetails), chatChoice.FinishDetails },
            { nameof(chatChoice.LogProbabilityInfo), chatChoice.LogProbabilityInfo },
            { nameof(chatChoice.Index), chatChoice.Index },
            { nameof(chatChoice.Enhancements), chatChoice.Enhancements },
        };
    }
    */

    private static Dictionary<string, object?> GetResponseMetadata(StreamingChatCompletionUpdate completions)
    {
        return new Dictionary<string, object?>(4)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.CreatedAt), completions.CreatedAt },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completions.FinishReason), completions.FinishReason?.ToString() },
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
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    internal async Task<IList<ReadOnlyMemory<float>>> GetEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        int? dimensions,
        CancellationToken cancellationToken)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);

        if (data.Count > 0)
        {
            var embeddingsOptions = new EmbeddingGenerationOptions()
            {
                Dimensions = dimensions
            };

            ClientResult<EmbeddingCollection> response = await RunRequestAsync(() => this.Client.GetEmbeddingClient(this.ModelName).GenerateEmbeddingsAsync(data, embeddingsOptions)).ConfigureAwait(false);
            var embeddings = response.Value;

            if (embeddings.Count != data.Count)
            {
                throw new KernelException($"Expected {data.Count} text embedding(s), but received {embeddings.Count}");
            }

            for (var i = 0; i < embeddings.Count; i++)
            {
                result.Add(embeddings[i].Vector);
            }
        }

        return result;
    }

    internal async Task<IReadOnlyList<TextContent>> GetTextContentFromAudioAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(content.Data);

        OpenAIAudioToTextExecutionSettings? audioExecutionSettings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings);
        AudioTranscriptionOptions? audioOptions = AudioOptionsFromExecutionSettings(executionSettings);

        Verify.ValidFilename(audioExecutionSettings?.Filename);

        var memoryStream = new MemoryStream(content.Data.Value.ToArray());

        AudioTranscription responseData = (await RunRequestAsync(() => this.Client.GetAudioClient(this.ModelName).TranscribeAudioAsync(memoryStream, audioExecutionSettings?.Filename, audioOptions)).ConfigureAwait(false)).Value;

        return [new(responseData.Text, this.ModelName, metadata: GetResponseMetadata(responseData))];
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to derived <see cref="OpenAIAudioToTextExecutionSettings"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="OpenAIAudioToTextExecutionSettings"/>.</returns>
    private static AudioTranscriptionOptions? AudioOptionsFromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new AudioTranscriptionOptions();
        }

        if (executionSettings is OpenAIAudioToTextExecutionSettings settings)
        {
            return new AudioTranscriptionOptions
            {
                Granularities = ConvertToAudioTimestampGranularities(settings.Granularities),
                Language = settings.Language,
                Prompt = settings.Prompt,
                Temperature = settings.Temperature
            };
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAIAudioToTextExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        if (openAIExecutionSettings is not null)
        {
            return new AudioTranscriptionOptions
            {
                Granularities = ConvertToAudioTimestampGranularities(openAIExecutionSettings.Granularities),
                Language = openAIExecutionSettings.Language,
                Prompt = openAIExecutionSettings.Prompt,
                Temperature = openAIExecutionSettings.Temperature
            };
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(OpenAIAudioToTextExecutionSettings)}", nameof(executionSettings));
    }

    private static AudioTimestampGranularities ConvertToAudioTimestampGranularities(OpenAIAudioToTextExecutionSettings.TimeStampGranularities[]? granularity)
    {
        return granularity?.FirstOrDefault() switch
        {
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Default => AudioTimestampGranularities.Default,
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Word => AudioTimestampGranularities.Word,
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Segment => AudioTimestampGranularities.Segment,
            _ => AudioTimestampGranularities.Default
        };
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chatProvided">Chat history</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Generated chat message in string format</returns>
    internal async Task<ChatMessageContent> GetChatMessageContentsAsync(
        ChatHistory chatProvided,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatProvided);

        // Convert the incoming execution settings to OpenAI settings.
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        bool autoInvoke = kernel is not null && chatExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0 && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;
        ValidateMaxTokens(chatExecutionSettings.MaxTokens);
        ValidateAutoInvoke(autoInvoke, chatExecutionSettings.ResultsPerPrompt);

        /// Create the OpenAI SDK <see cref="ChatCompletionOptions"/> instance from all available information.
        var (chatOptions, chatForRequest) = this.CreateChatCompletionsOptions(chatExecutionSettings, chatProvided, kernel, this.ModelName);
        for (int requestIndex = 1; ; requestIndex++)
        {
            // Make the request.
            OpenAIChatCompletion? responseData = null;
            OpenAIChatMessageContent responseContent;
            using (var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.ModelName, ModelProvider, chatProvided, chatExecutionSettings))
            {
                try
                {
                    responseData = (await RunRequestAsync(() => this.Client.GetChatClient(this.ModelName).CompleteChatAsync(chatForRequest, chatOptions)).ConfigureAwait(false)).Value;
                    this.LogUsage(responseData.Usage);
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    if (responseData != null)
                    {
                        // Capture available metadata even if the operation failed.
                        activity
                            .SetResponseId(responseData.Id)
                            .SetPromptTokenUsage(responseData.Usage.InputTokens)
                            .SetCompletionTokenUsage(responseData.Usage.OutputTokens);
                    }
                    throw;
                }

                responseContent = new OpenAIChatMessageContent(responseData);
                activity?.SetCompletionResponse([responseContent], responseData.Usage.InputTokens, responseData.Usage.OutputTokens);
            }

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!autoInvoke)
            {
                return responseContent;
            }

            Debug.Assert(kernel is not null);

            // Get our single result and extract the function call information. If this isn't a function call, or if it is
            // but we're unable to find the function or extract the relevant information, just return the single result.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            var result = new OpenAIChatMessageContent(responseData);
            if (result.ToolCalls.Count == 0)
            {
                return result;
            }

            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Tool requests: {Requests}", result.ToolCalls.Count);
            }
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", result.ToolCalls.OfType<ChatToolCall>().Select(ftc => $"{ftc.FunctionName}({ftc.FunctionArguments})")));
            }

            var resultMessage = result.Content;

            // Add the original assistant message to the chatOptions; this is required for the service
            // to understand the tool call responses. Also add the result message to the caller's chat
            // history: if they don't want it, they can remove it, but this makes the data available,
            // including metadata like usage.
            chatForRequest.Add(GetRequestMessage(responseData));
            chatProvided.Add(result);

            // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
            // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
            for (int toolCallIndex = 0; toolCallIndex < result.ToolCalls.Count; toolCallIndex++)
            {
                ChatToolCall toolCall = result.ToolCalls[toolCallIndex];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (toolCall.Kind != ChatToolCallKind.Function)
                {
                    AddResponseMessage(chatOptions, chatForRequest, chatProvided, result: null, "Error: Tool call was not a function call.", toolCall, this.Logger);
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
                    AddResponseMessage(chatOptions, chatForRequest, chatProvided, result: null, "Error: Function call arguments were invalid JSON.", toolCall, this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatOptions, chatForRequest, chatProvided, result: null, "Error: Function call request for a function that wasn't defined.", toolCall, this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatOptions, chatForRequest, chatProvided, result: null, "Error: Requested function could not be found.", toolCall, this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                FunctionResult functionResult = new(function) { Culture = kernel.Culture };
                AutoFunctionInvocationContext invocationContext = new(kernel, function, functionResult, chatProvided)
                {
                    Arguments = functionArgs,
                    RequestSequenceIndex = requestIndex - 1,
                    FunctionSequenceIndex = toolCallIndex,
                    FunctionCount = result.ToolCalls.Count
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
                    AddResponseMessage(chatOptions, chatForRequest, chatProvided, null, $"Error: Exception while invoking function. {e.Message}", toolCall, this.Logger);
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

                AddResponseMessage(chatOptions, chatForRequest, chatProvided, stringResult, errorMessage: null, toolCall, this.Logger);

                // If filter requested termination, returning latest function result.
                if (invocationContext.Terminate)
                {
                    if (this.Logger.IsEnabled(LogLevel.Debug))
                    {
                        this.Logger.LogDebug("Filter requested termination of automatic function invocation.");
                    }

                    return chatProvided.Last();
                }

                static void AddResponseMessage(ChatCompletionOptions chatOptions, List<ChatMessage> openAIRequestChatHistory, ChatHistory chat, string? result, string? errorMessage, ChatToolCall toolCall, ILogger logger)
                {
                    // Log any error
                    if (errorMessage is not null && logger.IsEnabled(LogLevel.Debug))
                    {
                        Debug.Assert(result is null);
                        logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", toolCall.Id, errorMessage);
                    }

                    // Add the tool response message to the chat options
                    result ??= errorMessage ?? string.Empty;
                    openAIRequestChatHistory.Add(ChatMessage.CreateToolChatMessage(toolCall.Id, result));

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
            }

            // Update tool use information for the next go-around based on having completed another iteration.
            Debug.Assert(chatExecutionSettings.ToolCallBehavior is not null);

            // Set the tool choice to none. If we end up wanting to use tools, we'll reset it to the desired value.
            chatOptions = chatOptions.CloneWith(ChatToolChoice.None);
            chatOptions.Tools.Clear();

            if (requestIndex >= chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
            {
                // Don't add any tools as we've reached the maximum attempts limit.
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
                }
            }
            else
            {
                // Regenerate the tool list as necessary. The invocation of the function(s) could have augmented
                // what functions are available in the kernel.
                chatExecutionSettings.ToolCallBehavior.ConfigureOptions(kernel, chatOptions);
            }

            // Having already sent tools and with tool call information in history, the service can become unhappy ("[] is too short - 'tools'")
            // if we don't send any tools in subsequent requests, even if we say not to use any.
            if (chatOptions.ToolChoice == ChatToolChoice.None)
            {
                Debug.Assert(chatOptions.Tools.Count == 0);
                chatOptions.Tools.Add(s_nonInvocableFunctionTool);
            }

            // Disable auto invocation if we've exceeded the allowed limit.
            if (requestIndex >= chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
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

        var (chatOptions, chatForRequest) = this.CreateChatCompletionsOptions(chatExecutionSettings, chat, kernel, this.ModelName);

        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;

        for (int requestIndex = 1; ; requestIndex++)
        {
            // Reset state
            contentBuilder?.Clear();
            toolCallIdsByIndex?.Clear();
            functionNamesByIndex?.Clear();
            functionArgumentBuildersByIndex?.Clear();

            // Stream the response.
            IReadOnlyDictionary<string, object?>? metadata = null;
            ChatMessageRole? streamedRole = default;
            ChatFinishReason finishReason = default;
            ChatToolCall[]? toolCalls = null;
            FunctionCallContent[]? functionCallContents = null;

            using (var activity = ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.ModelName, ModelProvider, chat, chatExecutionSettings))
            {
                // Make the request.
                AsyncResultCollection<StreamingChatCompletionUpdate> response;
                try
                {
                    response = this.Client.GetChatClient(this.ModelName).CompleteChatStreamingAsync(chatForRequest, chatOptions);
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

                        StreamingChatCompletionUpdate update = responseEnumerator.Current;
                        metadata = GetResponseMetadata(update);
                        streamedRole ??= update.Role;
                        finishReason = update.FinishReason ?? default;

                        // If we're intending to invoke function calls, we need to consume that function call information.
                        if (autoInvoke)
                        {
                            var textUpdate = update.ContentUpdate.FirstOrDefault(u => u.Kind == ChatMessageContentPartKind.Text)?.Text;
                            if (textUpdate is { Length: > 0 })
                            {
                                (contentBuilder ??= new()).Append(textUpdate);
                            }

                            foreach (var toolCall in update.ToolCallUpdates)
                            {
                                if (toolCall.Kind == ChatToolCallKind.Function)
                                {
                                    OpenAIFunctionToolCall.TrackStreamingToolingUpdate(toolCall, ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);
                                }
                            }
                        }

                        var openAIStreamingChatMessageContent = new OpenAIStreamingChatMessageContent(update, 0, this.ModelName, metadata);
                        streamedContents?.Add(openAIStreamingChatMessageContent);
                        yield return openAIStreamingChatMessageContent;
                    }

                    // Translate all entries into ChatCompletionsFunctionToolCall instances.
                    toolCalls = OpenAIFunctionToolCall.ConvertToolCallsToChatToolCalls(ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);
                    // Translate all entries into FunctionCallContent instances for diagnostics purposes.
                    functionCallContents = ModelDiagnostics.IsSensitiveEventsEnabled() ? toolCalls.Select(toolCall => GetFunctionCallContent(toolCall, this.Logger)).ToArray() : null;
                }
                finally
                {
                    activity?.EndStreaming(streamedContents, functionCallContents);
                    await responseEnumerator.DisposeAsync();
                }
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

            // Log the requests
            if (this.Logger.IsEnabled(LogLevel.Trace))
            {
                this.Logger.LogTrace("Function call requests: {Requests}", string.Join(", ", toolCalls.Select(fcr => $"{fcr.FunctionName}({fcr.FunctionArguments})")));
            }
            else if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Function call requests: {Requests}", toolCalls.Length);
            }

            // Add the original assistant message to the chatOptions; this is required for the service
            // to understand the tool call responses.
            chatForRequest.Add(GetRequestMessage(streamedRole ?? default, content, null, toolCalls));
            // Add the result message to the caller's chat history
            var newChatMessageContent = new OpenAIChatMessageContent(streamedRole ?? default, content, this.ModelName, toolCalls, metadata);
            // Add the tool call messages to the new chat message content for diagnostics purposes.
            foreach (var functionCall in functionCallContents ?? [])
            {
                newChatMessageContent.Items.Add(functionCall);
            }
            chat.Add(newChatMessageContent);

            // Respond to each tooling request.
            for (int toolCallIndex = 0; toolCallIndex < toolCalls.Length; toolCallIndex++)
            {
                ChatToolCall toolCall = toolCalls[toolCallIndex];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (string.IsNullOrEmpty(toolCall.FunctionName))
                {
                    AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, result: null, "Error: Tool call was not a function call.", this.Logger);
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
                    AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, result: null, "Error: Function call arguments were invalid JSON.", this.Logger);
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (chatExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatOptions, openAIFunctionToolCall))
                {
                    AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, result: null, "Error: Function call request for a function that wasn't defined.", this.Logger);
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(openAIFunctionToolCall, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, result: null, "Error: Requested function could not be found.", this.Logger);
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                FunctionResult functionResult = new(function) { Culture = kernel.Culture };
                AutoFunctionInvocationContext invocationContext = new(kernel, function, functionResult, chat)
                {
                    Arguments = functionArgs,
                    RequestSequenceIndex = requestIndex - 1,
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
                    AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, result: null, $"Error: Exception while invoking function. {e.Message}", this.Logger);
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

                AddResponseMessage(chatOptions, chatForRequest, chat, streamedRole, toolCall, metadata, stringResult, errorMessage: null, this.Logger);

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

                static void AddResponseMessage(
                    ChatCompletionOptions chatOptions, List<ChatMessage> chatForRequest, ChatHistory chat, ChatMessageRole? streamedRole, ChatToolCall tool, IReadOnlyDictionary<string, object?>? metadata,
                    string? result, string? errorMessage, ILogger logger)
                {
                    if (errorMessage is not null && logger.IsEnabled(LogLevel.Debug))
                    {
                        Debug.Assert(result is null);
                        logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", tool.Id, errorMessage);
                    }

                    // Add the tool response message to both the chat options and to the chat history.
                    result ??= errorMessage ?? string.Empty;
                    chatForRequest.Add(ChatMessage.CreateToolChatMessage(tool.Id, result));
                    chat.AddMessage(AuthorRole.Tool, result, metadata: new Dictionary<string, object?> { { OpenAIChatMessageContent.ToolIdProperty, tool.Id } });
                }
            }

            // Update tool use information for the next go-around based on having completed another iteration.
            Debug.Assert(chatExecutionSettings.ToolCallBehavior is not null);

            // Set the tool choice to none. If we end up wanting to use tools, we'll reset it to the desired value.
            chatOptions = chatOptions.CloneWith(ChatToolChoice.None);
            chatOptions.Tools.Clear();

            if (requestIndex >= chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
            {
                // Don't add any tools as we've reached the maximum attempts limit.
                if (this.Logger.IsEnabled(LogLevel.Debug))
                {
                    this.Logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", chatExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
                }
            }
            else
            {
                // Regenerate the tool list as necessary. The invocation of the function(s) could have augmented
                // what functions are available in the kernel.
                chatExecutionSettings.ToolCallBehavior.ConfigureOptions(kernel, chatOptions);
            }

            // Having already sent tools and with tool call information in history, the service can become unhappy ("[] is too short - 'tools'")
            // if we don't send any tools in subsequent requests, even if we say not to use any.
            if (chatOptions.ToolChoice == ChatToolChoice.None)
            {
                Debug.Assert(chatOptions.Tools.Count == 0);
                chatOptions.Tools.Add(s_nonInvocableFunctionTool);
            }

            // Disable auto invocation if we've exceeded the allowed limit.
            if (requestIndex >= chatExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
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
    private static bool IsRequestableTool(ChatCompletionOptions options, OpenAIFunctionToolCall ftc)
    {
        IList<ChatTool> tools = options.Tools;
        for (int i = 0; i < tools.Count; i++)
        {
            var def = tools[i];
            if (def.Kind == ChatToolKind.Function && string.Equals(def.FunctionName, ftc.FullyQualifiedName, StringComparison.OrdinalIgnoreCase))
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

        await foreach (var chatUpdate in this.GetStreamingChatMessageContentsAsync(chat, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(chatUpdate.Content, chatUpdate.ChoiceIndex, chatUpdate.ModelId, chatUpdate, Encoding.UTF8, chatUpdate.Metadata);
        }
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
            ApplicationId = HttpHeaderConstant.Values.UserAgent,
        };

        options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore))), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable SDK retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable SDK default timeout
        }

        return options;
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

    private (ChatCompletionOptions, List<ChatMessage>) CreateChatCompletionsOptions(
        OpenAIPromptExecutionSettings executionSettings,
        ChatHistory chatHistory,
        Kernel? kernel,
        string deploymentOrModelName)
    {
        if (executionSettings.ResultsPerPrompt is < 1 or > MaxResultsPerPrompt)
        {
            throw new ArgumentOutOfRangeException($"{nameof(executionSettings)}.{nameof(executionSettings.ResultsPerPrompt)}", executionSettings.ResultsPerPrompt, $"The value must be in range between 1 and {MaxResultsPerPrompt}, inclusive.");
        }

        if (this.Logger.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        /* Unmerged change from project 'Connectors.OpenAIV2(netstandard2.0)'
        Before:
                ChatResponseFormat? responseFormat = null; 
        After:
                ChatResponseFormat? responseFormat = null;
        */
        ChatResponseFormat? responseFormat = null;
        switch (executionSettings.ResponseFormat)
        {
            case string formatString:
                // If the response format is a string, map the ones we know about, and ignore the rest.
                switch (formatString)
                {
                    case "json_object":
                        responseFormat = ChatResponseFormat.JsonObject;
                        break;

                    case "text":
                        responseFormat = ChatResponseFormat.Text;
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
                            responseFormat = ChatResponseFormat.JsonObject;
                            break;

                        case "text":
                            responseFormat = ChatResponseFormat.Text;
                            break;
                    }
                }
                break;
        }

        var options = new ChatCompletionOptions
        {
            MaxTokens = executionSettings.MaxTokens,
            Temperature = (float?)executionSettings.Temperature,
            TopP = (float?)executionSettings.TopP,
            FrequencyPenalty = (float?)executionSettings.FrequencyPenalty,
            PresencePenalty = (float?)executionSettings.PresencePenalty,
            // ChoiceCount = executionSettings.ResultsPerPrompt,
            Seed = executionSettings.Seed,
            User = executionSettings.User,
            TopLogProbabilityCount = executionSettings.TopLogprobs,
            IncludeLogProbabilities = executionSettings.Logprobs,
            ResponseFormat = responseFormat,
        };

        executionSettings.ToolCallBehavior?.ConfigureOptions(kernel, options);
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

        var openAIChatHistory = new List<ChatMessage>();
        if (!string.IsNullOrWhiteSpace(executionSettings.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            openAIChatHistory.AddRange(GetRequestMessages(new ChatMessageContent(AuthorRole.System, executionSettings!.ChatSystemPrompt), executionSettings.ToolCallBehavior));
        }

        foreach (var message in chatHistory)
        {
            openAIChatHistory.AddRange(GetRequestMessages(message, executionSettings.ToolCallBehavior));
        }

        return (options, openAIChatHistory);
    }

    private static ChatMessage GetRequestMessage(ChatMessageRole chatRole, string contents, string? name, ChatToolCall[]? tools)
    {
        if (chatRole == ChatMessageRole.User)
        {
            return new UserChatMessage(contents) { ParticipantName = name };
        }

        if (chatRole == ChatMessageRole.System)
        {
            return new SystemChatMessage(contents) { ParticipantName = name };
        }

        if (chatRole == ChatMessageRole.Assistant)
        {
            return new AssistantChatMessage(tools, contents) { ParticipantName = name };
        }

        throw new NotImplementedException($"Role {chatRole} is not implemented");
    }

    private static ChatMessage GetRequestMessage(OpenAIChatCompletion message)
    {
        if (message.Role == ChatMessageRole.System)
        {
            var systemMessage = message.Content.FirstOrDefault(c => c.Kind == ChatMessageContentPartKind.Text)?.Text;
            return ChatMessage.CreateSystemMessage(systemMessage);
        }

        if (message.Role == ChatMessageRole.Assistant)
        {
            return ChatMessage.CreateAssistantMessage(message);
        }

        if (message.Role == ChatMessageRole.User)
        {
            return ChatMessage.CreateUserMessage(message.Content);
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static List<ChatMessage> GetRequestMessages(ChatMessageContent message, ToolCallBehavior? toolCallBehavior)
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
                return [ChatMessage.CreateToolChatMessage(toolIdString, message.Content)];
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
                    toolMessages.Add(ChatMessage.CreateToolChatMessage(resultContent.Id, $"Error: Exception while invoking function. {ex.Message}"));
                    continue;
                }

                var stringResult = ProcessFunctionResult(resultContent.Result ?? string.Empty, toolCallBehavior);

                toolMessages.Add(ChatMessage.CreateToolChatMessage(resultContent.Id, stringResult ?? string.Empty));
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

            return [new UserChatMessage(
                    message.Items.Select(static (KernelContent item) => (ChatMessageContentPart)(item switch
                    {
                        TextContent textContent => ChatMessageContentPart.CreateTextMessageContentPart(textContent.Text),
                        ImageContent imageContent => GetImageContentItem(imageContent),
                        _ => throw new NotSupportedException($"Unsupported chat message content type '{item.GetType()}'.")
                    }
                )))
            {
                ParticipantName = message.AuthorName
            }];
        }

        if (message.Role == AuthorRole.Assistant)
        {
            var asstMessage = new AssistantChatMessage(message.Content) { ParticipantName = message.AuthorName };

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
                asstMessage.ToolCalls.AddRange(tools);
            }

            // Handling function calls supplied via ChatMessageContent.Items collection elements of the FunctionCallContent type.
            HashSet<string>? functionCallIds = null;
            foreach (var item in message.Items)
            {
                if (item is not FunctionCallContent callRequest)
                {
                    continue;
                }

                functionCallIds ??= new HashSet<string>(asstMessage.ToolCalls.Select(t => t.Id));

                if (callRequest.Id is null || functionCallIds.Contains(callRequest.Id))
                {
                    continue;
                }

                var argument = JsonSerializer.Serialize(callRequest.Arguments);

                asstMessage.ToolCalls.Add(ChatToolCall.CreateFunctionToolCall(callRequest.Id, FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OpenAIFunction.NameSeparator), argument ?? string.Empty));
            }

            return [asstMessage];
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

    private OpenAIChatMessageContent GetChatMessage(OpenAIChatCompletion responseData)
    {
        var message = new OpenAIChatMessageContent(responseData);

        foreach (var toolCall in responseData.ToolCalls)
        {
            // Adding items of 'FunctionCallContent' type to the 'Items' collection even though the function calls are available via the 'ToolCalls' property.
            // This allows consumers to work with functions in an LLM-agnostic way.
            if (toolCall is ChatToolCall functionToolCall)
            {
                var functionCallContent = GetFunctionCallContent(functionToolCall, this.Logger);
                message.Items.Add(functionCallContent);
            }
        }

        return message;
    }

    internal static FunctionCallContent GetFunctionCallContent(ChatToolCall toolCall, ILogger? logger = null)
    {
        KernelArguments? arguments = null;
        Exception? exception = null;
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

            if (logger is not null && logger.IsEnabled(LogLevel.Debug))
            {
                logger.LogDebug(ex, "Failed to deserialize function arguments ({FunctionName}/{FunctionId}).", toolCall.FunctionName, toolCall.Id);
            }
        }

        var functionName = FunctionName.Parse(toolCall.FunctionName, OpenAIFunction.NameSeparator);

        return new FunctionCallContent(
            functionName: functionName.Name,
            pluginName: functionName.PluginName,
            id: toolCall.Id,
            arguments: arguments)
        {
            InnerContent = toolCall,
            Exception = exception
        };
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
        catch (ClientResultException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    /// <param name="usage">Instance of <see cref="ChatTokenUsage"/> with usage details.</param>
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
                "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}.",
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
}
