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
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.Diagnostics;
using OllamaSharp;
using OllamaSharp.Models.Chat;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a chat completion service using Ollama Original API.
/// </summary>
public sealed class OllamaChatCompletionService : ServiceBase, IChatCompletionService
{
    /// <summary>
    /// Gets the metadata key for the tool id.
    /// </summary>
    public static string ToolIdProperty => "ChatCompletionsToolCall.Id";

    private const string ModelPlatform = "ollama";

    /// <summary>Gets the separator used between the plugin name and the function name, if a plugin name is present.</summary>
    /// <remarks>This separator was previously <c>_</c>, but has been changed to <c>-</c> to better align to the behavior elsewhere in SK and in response
    /// to developers who want to use underscores in their function or plugin names. We plan to make this setting configurable in the future.</remarks>
    public static string FunctionNameSeparator { get; set; } = "-";

    // Keeping private as Ollama currently only supports auto choice.
    // See: https://github.com/ollama/ollama/blob/main/docs/openai.md#supported-request-fields
    private enum ChatToolChoice
    {
        Auto
    }

    private static readonly KernelJsonSchema s_stringNoDescriptionSchema = KernelJsonSchema.Parse("""{"type":"string"}""");

    private record ToolCallingConfig(IList<Tool>? Tools, ChatToolChoice? Choice, bool AutoInvoke, bool AllowAnyRequestedKernelFunction, FunctionChoiceBehaviorOptions? Options);

    /// <summary>
    /// The function calls processor.
    /// </summary>
    private readonly FunctionCallsProcessor _functionCallsProcessor;

    /// <summary>
    /// Cached JSON for a function with no parameters.
    /// </summary>
    /// <remarks>
    /// This is an optimization to avoid serializing the same JSON Schema over and over again
    /// for this relatively common case.
    /// </remarks>
    private readonly static Parameters s_zeroFunctionParametersSchema = new() { Properties = [], Required = [] };

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string modelId,
        Uri endpoint,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, endpoint, null, loggerFactory?.CreateLogger(typeof(OllamaChatCompletionService)))
    {
        Verify.NotNull(endpoint);

        this._functionCallsProcessor = new FunctionCallsProcessor(this.Logger);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="httpClient">HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string modelId,
        HttpClient httpClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, null, httpClient, loggerFactory?.CreateLogger(typeof(OllamaChatCompletionService)))
    {
        Verify.NotNull(httpClient);
        Verify.NotNull(httpClient.BaseAddress);

        this._functionCallsProcessor = new FunctionCallsProcessor(this.Logger);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string modelId,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, ollamaClient, loggerFactory?.CreateLogger(typeof(OllamaChatCompletionService)))
    {
        this._functionCallsProcessor = new FunctionCallsProcessor(this.Logger);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    /// <param name="usage">Instance of <see cref="ChatDoneResponseStream"/> with token usage details.</param>
    private void LogUsage(ChatDoneResponseStream? usage)
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
                usage.PromptEvalCount, usage.EvalCount, usage.PromptEvalCount + usage.EvalCount);
        }

        s_promptTokensCounter.Add(usage.PromptEvalCount);
        s_completionTokensCounter.Add(usage.EvalCount);
        s_totalTokensCounter.Add(usage.PromptEvalCount + usage.EvalCount);
    }

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel.Connectors.Ollama");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    private static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.ollama.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    private static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.ollama.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    private static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.ollama.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    /// <inheritdoc />
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Ollama accepts empty chat history to trigger Model Loading https://github.com/ollama/ollama/blob/main/docs/api.md#load-a-model-1
        chatHistory ??= [];

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        var chatExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        for (int requestIndex = 0; ; requestIndex++)
        {
            var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chatHistory);
            var toolCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, requestIndex);
            var request = CreateChatRequest(chatForRequest, chatHistory, chatExecutionSettings, this._client.SelectedModel, toolCallingConfig);
            request.Stream = false;

            var chatMessageContent = new ChatMessageContent();

            ChatDoneResponseStream? singleDoneChunk = null;
            using (var activity = this.StartCompletionActivity(chatHistory, chatExecutionSettings))
            {
                try
                {
                    var enumerator = this._client.Chat(request, cancellationToken).GetAsyncEnumerator(cancellationToken);
                    await enumerator.MoveNextAsync().ConfigureAwait(false);
                    // When streaming is false in the configuration, we expect the first chunk to be the full response.
                    singleDoneChunk = enumerator.Current as ChatDoneResponseStream;

                    this.LogUsage(singleDoneChunk);
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetError(ex);
                    if (singleDoneChunk != null)
                    {
                        // Capture available metadata even if the operation failed.
                        activity
                            .SetResponseId(singleDoneChunk.CreatedAt)
                            .SetPromptTokenUsage(singleDoneChunk.PromptEvalCount)
                            .SetCompletionTokenUsage(singleDoneChunk.EvalCount);
                    }

                    throw;
                }

                chatMessageContent = this.CreateChatMessageContent(singleDoneChunk!);
                activity?.SetCompletionResponse([chatMessageContent], singleDoneChunk.PromptEvalCount, singleDoneChunk.EvalCount);
            }

            var toolCallsCount = singleDoneChunk!.Message.ToolCalls?.Count() ?? 0;
            // If we don't want to attempt to invoke any functions or there is nothing to call, just return the result.
            if (!toolCallingConfig.AutoInvoke || toolCallsCount == 0)
            {
                return [chatMessageContent];
            }

            // Process function calls by invoking the functions and adding the results to the chat history.
            // Each function call will trigger auto-function-invocation filters, which can terminate the process.
            // In such cases, we'll return the last message in the chat history.
            var lastMessage = await this._functionCallsProcessor.ProcessFunctionCallsAsync(
                chatMessageContent,
                chatHistory,
                requestIndex,
                (FunctionCallContent content) => IsRequestableTool(request.Tools, content),
                kernel,
                cancellationToken).ConfigureAwait(false);
            if (lastMessage != null)
            {
                return [lastMessage];
            }
        }
    }

    private ChatMessageContent CreateChatMessageContent(ChatDoneResponseStream completion)
    {
        var message = new ChatMessageContent(
            role: GetAuthorRole(completion.Message.Role)!.Value,
            items: new ChatMessageContentItemCollection())
        {
            ModelId = completion.Model,
            InnerContent = completion,
            Metadata = GetChatCompletionMetadata(completion)
        };

        if (!string.IsNullOrEmpty(completion.Message.Content))
        {
            message.Content = completion.Message.Content ?? string.Empty;
        }

        message.Items.AddRange(this.GetFunctionCallContents(completion.Message.ToolCalls));

        return message;
    }

    private List<FunctionCallContent> GetFunctionCallContents(IEnumerable<Message.ToolCall>? toolCalls)
    {
        List<FunctionCallContent> result = [];

        if (toolCalls is null)
        {
            return result;
        }

        foreach (var toolCall in toolCalls)
        {
            // Adding items of 'FunctionCallContent' type to the 'Items' collection even though the function calls are available via the 'ToolCalls' property.
            // This allows consumers to work with functions in an LLM-agnostic way.
            Exception? exception = null;
            KernelArguments? kernelArguments = null;
            var responseArguments = toolCall.Function!.Arguments;
            if (responseArguments is not null)
            {
                // Iterate over copy of the names to avoid mutating the dictionary while enumerating it
                var names = responseArguments.Keys.ToArray();
                foreach (var name in names)
                {
                    (kernelArguments ??= []).Add(name, responseArguments[name]);
                }
            }

            var functionName = FunctionName.Parse(toolCall.Function!.Name!, OllamaChatCompletionService.FunctionNameSeparator);

            var functionCallContent = new FunctionCallContent(
                functionName: functionName.Name,
                pluginName: functionName.PluginName,
                id: Guid.NewGuid().ToString().Substring(0, 8),
                arguments: kernelArguments)
            {
                InnerContent = toolCall,
                Exception = exception
            };

            result.Add(functionCallContent);
        }

        return result;
    }

    private static Dictionary<string, object?> GetChatCompletionMetadata(ChatDoneResponseStream doneChatUpdate)
    {
        return new Dictionary<string, object?>
            {
                // Necessary for the function telemetry 
                { "Usage", new {
                    PromptTokens = doneChatUpdate.PromptEvalCount,
                    CompletionTokens = doneChatUpdate.EvalCount
                }},
            };
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(IEnumerable<Tool>? tools, FunctionCallContent functionCallContent)
    {
        if (tools is null)
        {
            return false;
        }

        foreach (var tool in tools)
        {
            if (tool.Function?.Name is not null &&
                string.Equals(tool.Function!.Name, FunctionName.ToFullyQualifiedName(functionCallContent.FunctionName, functionCallContent.PluginName, OllamaChatCompletionService.FunctionNameSeparator), StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Start a chat completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    private Activity? StartCompletionActivity(ChatHistory chatHistory, PromptExecutionSettings settings)
        => ModelDiagnostics.StartCompletionActivity(this._client.Config.Uri, this._client.Config.Model, ModelPlatform, chatHistory, settings);

    /// <summary>
    /// Tracks tooling updates from streaming responses.
    /// </summary>
    /// <param name="updates">The tool call updates to incorporate.</param>
    /// <param name="toolCallIdsByIndex">Lazily-initialized dictionary mapping indices to IDs.</param>
    /// <param name="functionNamesByIndex">Lazily-initialized dictionary mapping indices to names.</param>
    /// <param name="functionArgumentBuildersByIndex">Lazily-initialized dictionary mapping indices to arguments.</param>
    internal static void TrackStreamingToolingUpdate(
        IEnumerable<Message.ToolCall>? updates,
        ref Dictionary<int, string>? toolCallIdsByIndex,
        ref Dictionary<int, string>? functionNamesByIndex,
        ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Ollama accepts empty chat history to trigger Model Loading https://github.com/ollama/ollama/blob/main/docs/api.md#load-a-model-1
        chatHistory ??= [];

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        var chatExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        StringBuilder? contentBuilder = null;
        var chatForRequest = CreateChatCompletionMessages(chatExecutionSettings, chatHistory);
        var toolCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, 0);

        if (toolCallingConfig.Tools is { Count: > 0 })
        {
            throw new NotSupportedException(
                "Currently, Ollama does not support function calls in streaming mode. " +
                "See Ollama docs at https://github.com/ollama/ollama/blob/main/docs/api.md#parameters-1 to see whether support has since been added.");
        }

        var request = CreateChatRequest(chatForRequest, chatHistory, chatExecutionSettings, this._client.SelectedModel, toolCallingConfig);

        // Reset state
        contentBuilder?.Clear();

        // Stream the response.
        IReadOnlyDictionary<string, object?>? metadata = null;
        ChatRole? streamedRole = default;
        string? streamedDoneReason = null;

        IAsyncEnumerable<ChatResponseStream?> response;
        using (var activity = this.StartCompletionActivity(chatHistory, chatExecutionSettings))
        {
            try
            {
                response = this._client.Chat(request, cancellationToken);
            }
            catch (Exception ex) when (activity is not null)
            {
                activity.SetError(ex);
                throw;
            }

            var responseEnumerator = response.GetAsyncEnumerator(cancellationToken);
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

                    ChatResponseStream? updateChunk = responseEnumerator.Current;
                    if (updateChunk is null)
                    {
                        continue;
                    }

                    streamedRole ??= updateChunk.Message.Role;
                    if (updateChunk is ChatDoneResponseStream doneUpdate)
                    {
                        streamedDoneReason ??= doneUpdate.DoneReason;
                        metadata = GetChatCompletionMetadata(doneUpdate);
                    }

                    // If we're intending to invoke function calls, we need to consume that function call information.
                    if (toolCallingConfig.AutoInvoke || (updateChunk.Message.ToolCalls?.Any() ?? false))
                    {
                        throw new NotSupportedException(
                            "Currently, Ollama does not support function calls in streaming mode. " +
                            "See Ollama docs at https://github.com/ollama/ollama/blob/main/docs/api.md#parameters-1 to see whether support has since been added.");
                    }

                    var streamingChatMessageContent = new StreamingChatMessageContent(GetAuthorRole(streamedRole), updateChunk.Message.Content)
                    {
                        Metadata = metadata,
                        InnerContent = updateChunk,
                        ModelId = updateChunk.Model
                    };

                    streamedContents?.Add(streamingChatMessageContent);
                    yield return streamingChatMessageContent;
                }

                // Translate all entries into ChatCompletionsFunctionToolCall instances.
                // toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToFunctionToolCalls(
                //     ref toolCallIdsByIndex, ref functionNamesByIndex, ref functionArgumentBuildersByIndex);

                // Translate all entries into FunctionCallContent instances for diagnostics purposes.
                // functionCallContents = this.GetFunctionCallContents(toolCalls).ToArray();
            }
            finally
            {
                activity?.EndStreaming(streamedContents, null);
                await responseEnumerator.ConfigureAwait(false).DisposeAsync();
            }
        }
    }

    private ToolCallingConfig GetFunctionCallingConfiguration(Kernel? kernel, OllamaPromptExecutionSettings executionSettings, ChatHistory chatHistory, int requestIndex)
    {
        // If neither behavior is specified, we just return default configuration with no tool and no choice
        if (executionSettings.FunctionChoiceBehavior is null)
        {
            return new ToolCallingConfig(Tools: null, Choice: null, AutoInvoke: false, AllowAnyRequestedKernelFunction: false, Options: null);
        }

        IList<Tool>? tools = null;
        ChatToolChoice? choice = null;
        bool autoInvoke = false;
        bool allowAnyRequestedKernelFunction = false;
        FunctionChoiceBehaviorOptions? options = null;

        // Handling new tool behavior represented by `PromptExecutionSettings.FunctionChoiceBehavior` property.
        if (executionSettings.FunctionChoiceBehavior is { } functionChoiceBehavior)
        {
            (tools, choice, autoInvoke, options) = this.ConfigureFunctionCalling(kernel, requestIndex, functionChoiceBehavior, chatHistory);
        }

        return new ToolCallingConfig(
            Tools: tools, // Ollama may be happy with null here
            Choice: choice ?? ChatToolChoice.Auto,
            AutoInvoke: autoInvoke,
            AllowAnyRequestedKernelFunction: allowAnyRequestedKernelFunction,
            Options: options);
    }

    private (IList<Tool>? Tools, ChatToolChoice? Choice, bool AutoInvoke, FunctionChoiceBehaviorOptions? Options) ConfigureFunctionCalling(Kernel? kernel, int requestIndex, FunctionChoiceBehavior functionChoiceBehavior, ChatHistory chatHistory)
    {
        FunctionChoiceBehaviorConfiguration? config = this._functionCallsProcessor.GetConfiguration(functionChoiceBehavior, chatHistory, requestIndex, kernel);

        IList<Tool>? tools = null;
        ChatToolChoice? toolChoice = null;
        bool autoInvoke = config?.AutoInvoke ?? false;

        if (config?.Functions is { Count: > 0 } functions)
        {
            if (config.Choice == FunctionChoice.Auto)
            {
                toolChoice = ChatToolChoice.Auto;
            }
            else
            {
                throw new NotSupportedException($"Unsupported function choice '{config.Choice}'.");
            }

            tools = [];

            foreach (var function in functions)
            {
                tools.Add(FromFunctionMetadata(function.Metadata));
            }
        }

        return new(tools, toolChoice, autoInvoke, config?.Options);
    }

    private static Tool FromFunctionMetadata(KernelFunctionMetadata functionMetadata)
    {
        IReadOnlyList<KernelParameterMetadata> metadataParams = functionMetadata.Parameters;
        Parameters resultParameters = s_zeroFunctionParametersSchema;

        var tool = new Tool()
        {
            Function = new Function
            {
                Name = FunctionName.ToFullyQualifiedName(functionMetadata.Name, functionMetadata.PluginName, OllamaChatCompletionService.FunctionNameSeparator),
                Description = functionMetadata.Description,
            }
        };

        if (metadataParams is { Count: > 0 })
        {
            var properties = new Dictionary<string, KernelJsonSchema>();
            var required = new List<string>();

            for (int i = 0; i < metadataParams.Count; i++)
            {
                var parameter = metadataParams[i];
                properties.Add(parameter.Name, parameter.Schema ?? GetDefaultSchemaForTypelessParameter(parameter.Description));
                if (parameter.IsRequired)
                {
                    required.Add(parameter.Name);
                }
            }

            string serializedParametersSchema = JsonSerializer.Serialize(new
            {
                type = "object",
                required,
                properties,
            });

            resultParameters = JsonSerializer.Deserialize<Parameters>(serializedParametersSchema)!;
        }

        tool.Function.Parameters = resultParameters;

        return tool;
    }

    /// <summary>Gets a <see cref="KernelJsonSchema"/> for a typeless parameter with the specified description, defaulting to typeof(string)</summary>
    private static KernelJsonSchema GetDefaultSchemaForTypelessParameter(string? description)
    {
        // If there's a description, incorporate it.
        if (!string.IsNullOrWhiteSpace(description))
        {
            return KernelJsonSchemaBuilder.Build(null, typeof(string), description);
        }

        // Otherwise, we can use a cached schema for a string with no description.
        return s_stringNoDescriptionSchema;
    }

    private static List<Message> CreateChatCompletionMessages(OllamaPromptExecutionSettings executionSettings, ChatHistory chatHistory)
    {
        List<Message> ollamaMessages = [];

        foreach (var chatMessageContent in chatHistory)
        {
            ollamaMessages.AddRange(CreateRequestMessages(chatMessageContent));
        }

        return ollamaMessages;
    }

    private static List<Message> CreateRequestMessages(ChatMessageContent message)
    {
        // If the abstraction message preserves the original Ollama message, use it as is.
        if (message.InnerContent is Message ollamaMessage)
        {
            return [ollamaMessage];
        }

        if (message.Role == AuthorRole.System)
        {
            return [new Message(ChatRole.System, message.Content ?? string.Empty)];
        }

        if (message.Role == AuthorRole.Tool)
        {
            // Handling function results represented by the TextContent type.
            // Example: new ChatMessageContent(AuthorRole.Tool, content, metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } })
            if (message.Metadata?.TryGetValue(OllamaChatCompletionService.ToolIdProperty, out object? toolId) is true &&
                toolId?.ToString() is string toolIdString)
            {
                return [new Message(ChatRole.Tool, message.Content ?? string.Empty)];
            }

            // Handling function results represented by the FunctionResultContent type.
            // Example: new ChatMessageContent(AuthorRole.Tool, items: new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) })
            List<Message>? toolMessages = null;
            foreach (var item in message.Items)
            {
                if (item is not FunctionResultContent resultContent)
                {
                    continue;
                }

                toolMessages ??= [];

                if (resultContent.Result is Exception ex)
                {
                    toolMessages.Add(new Message(ChatRole.Tool,
                        $"Error: Exception while invoking function. {ex.Message}"));
                    continue;
                }

                // resultContent.CallId, (No support for tool identifier ATM see: https://github.com/awaescher/OllamaSharp/issues/97)
                // for this reason the function result is serialized as one object with Id + Result.
                // This 
                var stringResult = JsonSerializer.Serialize(
                    new
                    {
                        tool_call_id = resultContent.CallId,
                        result = FunctionCallsProcessor.ProcessFunctionResult(resultContent.Result ?? string.Empty)
                    });

                toolMessages.Add(new Message(ChatRole.Tool, stringResult ?? string.Empty));
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
                return [new Message(ChatRole.User, textContent.Text ?? string.Empty)];
            }

            var messageResult = new Message() { Role = ChatRole.User };
            List<string> imageItems = [];

            foreach (var item in message.Items)
            {
                if (item is TextContent itemTextContent)
                {
                    messageResult.Content += itemTextContent.Text;
                    continue;
                }

                if (item is ImageContent itemImageContent)
                {
                    if (!itemImageContent.CanRead)
                    {
                        throw new NotSupportedException("Uri reference images is not supported, use images with binary image content.");
                    }

                    imageItems.Add(Convert.ToBase64String(itemImageContent.Data!.Value.ToArray()));
                }
            }

            if (imageItems.Count > 0)
            {
                messageResult.Images = imageItems.ToArray();
            }

            return [messageResult];
        }

        if (message.Role == AuthorRole.Assistant)
        {
            List<Message.ToolCall>? toolCallRequests = null;

            foreach (var item in message.Items)
            {
                if (item is not FunctionCallContent callRequest)
                {
                    continue;
                }

                var toolCallRequest = new Message.ToolCall
                {
                    Function = new Message.Function
                    {
                        Name = FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OllamaChatCompletionService.FunctionNameSeparator),
                        Arguments = new Dictionary<string, string>(),
                    },
                };

                if (callRequest.Arguments is not null)
                {
                    // Adapt to provide the call_id as an argument to the tool call
                    callRequest.Arguments.Add("call_id", callRequest.Id);
                    foreach (var callArgument in callRequest.Arguments)
                    {
                        toolCallRequest.Function.Arguments.Add(callArgument.Key, callArgument.Value?.ToString() ?? string.Empty);
                    }
                }

                (toolCallRequests ??= []).Add(toolCallRequest);
            }

            var assistantMessage = new Message()
            {
                Role = ChatRole.Assistant,
                ToolCalls = toolCallRequests,
                Content = message.Content ?? string.Empty
            };

            return [assistantMessage];
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    #region Private

    private static AuthorRole? GetAuthorRole(ChatRole? role) => role?.ToString().ToUpperInvariant() switch
    {
        "USER" => AuthorRole.User,
        "ASSISTANT" => AuthorRole.Assistant,
        "SYSTEM" => AuthorRole.System,
        null => null,
        _ => new AuthorRole(role.ToString()!)
    };

    private static ChatRequest CreateChatRequest(List<Message> chatForRequest, ChatHistory chatHistory, OllamaPromptExecutionSettings settings, string selectedModel, ToolCallingConfig toolCallingConfig)
    {
        var request = new ChatRequest
        {
            Options = new()
            {
                Temperature = settings.Temperature,
                TopP = settings.TopP,
                TopK = settings.TopK,
                Stop = settings.Stop?.ToArray()
            },
            Messages = chatForRequest,
            Model = selectedModel,
            Stream = true
        };

        if (toolCallingConfig.Tools is { Count: > 0 } tools)
        {
            request.Tools = tools;
        }

        return request;
    }

    #endregion
}
