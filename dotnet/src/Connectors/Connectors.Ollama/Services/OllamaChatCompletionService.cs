// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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

    /// <summary>Gets the separator used between the plugin name and the function name, if a plugin name is present.</summary>
    /// <remarks>This separator was previously <c>_</c>, but has been changed to <c>-</c> to better align to the behavior elsewhere in SK and in response
    /// to developers who want to use underscores in their function or plugin names. We plan to make this setting configurable in the future.</remarks>
    public static string FunctionNameSeparator { get; set; } = "-";

    /// <summary>
    /// Gets the metadata key for the list of <see cref="ChatToolCall"/>.
    /// </summary>
    internal static string FunctionToolCallsProperty => "ChatResponseMessage.FunctionToolCalls";

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
    private FunctionCallsProcessor _functionCallsProcessor;

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
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

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

            var functionCallingConfig = this.GetFunctionCallingConfiguration(kernel, chatExecutionSettings, chatHistory, requestIndex);


            var request = CreateChatRequest(chatHistory, chatExecutionSettings, this._client.SelectedModel);
            var chatMessageContent = new ChatMessageContent();
            var fullContent = new StringBuilder();
            string? modelId = null;
            AuthorRole? authorRole = null;
            List<ChatResponseStream> innerContent = [];

            await foreach (var responseStreamChunk in this._client.Chat(request, cancellationToken).ConfigureAwait(false))
            {
                if (responseStreamChunk is null)
                {
                    continue;
                }

                innerContent.Add(responseStreamChunk);

                if (responseStreamChunk.Message.Content is not null)
                {
                    fullContent.Append(responseStreamChunk.Message.Content);
                }

                if (responseStreamChunk.Message.Role is not null)
                {
                    authorRole = GetAuthorRole(responseStreamChunk.Message.Role)!.Value;
                }

                modelId ??= responseStreamChunk.Model;
            }
        }


        return [new ChatMessageContent(
            role: authorRole ?? new(),
            content: fullContent.ToString(),
            modelId: modelId,
            innerContent: innerContent)];
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
        List<Message> messages = [];

        foreach (var message in chatHistory)
        {
            messages.AddRange(CreateRequestMessages(message));
        }

        return messages;
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
                        // resultContent.CallId, (No support for tool identifier ATM see: https://github.com/awaescher/OllamaSharp/issues/97)
                        $"Error: Exception while invoking function. {ex.Message}"));
                    continue;
                }

                var stringResult = FunctionCalling.FunctionCallsProcessor.ProcessFunctionResult(resultContent.Result ?? string.Empty);

                toolMessages.Add(new Message(ChatRole.Tool,
                    // resultContent.CallId , (No support for tool identifier see: https://github.com/awaescher/OllamaSharp/issues/97)
                    stringResult ?? string.Empty));
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

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateChatRequest(chatHistory, settings, this._client.SelectedModel);

        await foreach (var message in this._client.Chat(request, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingChatMessageContent(
                role: GetAuthorRole(message!.Message.Role),
                content: message.Message.Content,
                modelId: message.Model,
                innerContent: message);
        }
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

    private static ChatRequest CreateChatRequest(ChatHistory chatHistory, OllamaPromptExecutionSettings settings, string selectedModel)
    {
        var messages = new List<Message>();
        foreach (var chatHistoryMessage in chatHistory)
        {
            ChatRole role = ChatRole.User;
            if (chatHistoryMessage.Role == AuthorRole.System)
            {
                role = ChatRole.System;
            }
            else if (chatHistoryMessage.Role == AuthorRole.Assistant)
            {
                role = ChatRole.Assistant;
            }

            messages.Add(new Message(role, chatHistoryMessage.Content!));
        }

        var request = new ChatRequest
        {
            Options = new()
            {
                Temperature = settings.Temperature,
                TopP = settings.TopP,
                TopK = settings.TopK,
                Stop = settings.Stop?.ToArray()
            },
            Messages = messages,
            Model = selectedModel,
            Stream = true
        };

        return request;
    }

    #endregion
}
