// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides an implementation of <see cref="IChatCompletionService"/> around an <see cref="IChatClient"/>.</summary>
internal sealed class ChatClientChatCompletionService : IChatCompletionService
{
    /// <summary>The wrapped <see cref="IChatClient"/>.</summary>
    private readonly IChatClient _chatClient;

    /// <summary>Initializes the <see cref="ChatClientChatCompletionService"/> for <paramref name="chatClient"/>.</summary>
    public ChatClientChatCompletionService(IChatClient chatClient, IServiceProvider? serviceProvider)
    {
        Verify.NotNull(chatClient);

        // Store the client.
        this._chatClient = chatClient;

        // Initialize the attributes.
        var attrs = new Dictionary<string, object?>();
        this.Attributes = new ReadOnlyDictionary<string, object?>(attrs);

        var metadata = chatClient.GetService<ChatClientMetadata>();
        if (metadata?.ProviderUri is not null)
        {
            attrs[AIServiceExtensions.EndpointKey] = metadata.ProviderUri.ToString();
        }
        if (metadata?.DefaultModelId is not null)
        {
            attrs[AIServiceExtensions.ModelIdKey] = metadata.DefaultModelId;
        }
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        var completion = await this._chatClient.GetResponseAsync(
            ChatCompletionServiceExtensions.ToChatMessageList(chatHistory),
            ToChatOptions(executionSettings, kernel),
            cancellationToken).ConfigureAwait(false);

        if (completion.Messages.Count > 0)
        {
            // Add all but the last message into the chat history.
            for (int i = 0; i < completion.Messages.Count - 1; i++)
            {
                chatHistory.Add(ChatCompletionServiceExtensions.ToChatMessageContent(completion.Messages[i], completion));
            }

            // Return the last message as the result.
            return [ChatCompletionServiceExtensions.ToChatMessageContent(completion.Messages[completion.Messages.Count - 1], completion)];
        }

        return [];
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatHistory);

        List<AIContent> fcContents = [];
        ChatRole? role = null;

        await foreach (var update in this._chatClient.GetStreamingResponseAsync(
            ChatCompletionServiceExtensions.ToChatMessageList(chatHistory),
            ToChatOptions(executionSettings, kernel),
            cancellationToken).ConfigureAwait(false))
        {
            role ??= update.Role;

            fcContents.AddRange(update.Contents.Where(c => c is Microsoft.Extensions.AI.FunctionCallContent or Microsoft.Extensions.AI.FunctionResultContent));

            yield return ToStreamingChatMessageContent(update);
        }

        // Add function call content/results to chat history, as other IChatCompletionService streaming implementations do.
        chatHistory.Add(ChatCompletionServiceExtensions.ToChatMessageContent(new ChatMessage(role ?? ChatRole.Assistant, fcContents)));
    }

    /// <summary>Converts a pair of <see cref="PromptExecutionSettings"/> and <see cref="Kernel"/> to a <see cref="ChatOptions"/>.</summary>
    private static ChatOptions? ToChatOptions(PromptExecutionSettings? settings, Kernel? kernel)
    {
        if (settings is null)
        {
            return null;
        }

        if (settings.GetType() != typeof(PromptExecutionSettings))
        {
            // If the settings are of a derived type, roundtrip through JSON to the base type in order to try
            // to get the derived strongly-typed properties to show up in the loosely-typed ExtensionData dictionary.
            // This has the unfortunate effect of making all the ExtensionData values into JsonElements, so we lose
            // some type fidelity. (As an alternative, we could introduce new interfaces that could be queried for
            // in this method and implemented by the derived settings types to control how they're converted to
            // ChatOptions.)
            settings = JsonSerializer.Deserialize(
                JsonSerializer.Serialize(settings, AbstractionsJsonContext.GetTypeInfo(settings.GetType(), null)),
                AbstractionsJsonContext.Default.PromptExecutionSettings);
        }

        ChatOptions options = new()
        {
            ModelId = settings!.ModelId
        };

        if (settings!.ExtensionData is IDictionary<string, object> extensionData)
        {
            foreach (var entry in extensionData)
            {
                if (entry.Key.Equals("temperature", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float temperature))
                {
                    options.Temperature = temperature;
                }
                else if (entry.Key.Equals("top_p", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float topP))
                {
                    options.TopP = topP;
                }
                else if (entry.Key.Equals("top_k", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out int topK))
                {
                    options.TopK = topK;
                }
                else if (entry.Key.Equals("seed", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out long seed))
                {
                    options.Seed = seed;
                }
                else if (entry.Key.Equals("max_tokens", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out int maxTokens))
                {
                    options.MaxOutputTokens = maxTokens;
                }
                else if (entry.Key.Equals("frequency_penalty", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float frequencyPenalty))
                {
                    options.FrequencyPenalty = frequencyPenalty;
                }
                else if (entry.Key.Equals("presence_penalty", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float presencePenalty))
                {
                    options.PresencePenalty = presencePenalty;
                }
                else if (entry.Key.Equals("stop_sequences", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out IList<string>? stopSequences))
                {
                    options.StopSequences = stopSequences;
                }
                else if (entry.Key.Equals("response_format", StringComparison.OrdinalIgnoreCase) &&
                    entry.Value is { } responseFormat)
                {
                    if (TryConvert(responseFormat, out string? responseFormatString))
                    {
                        options.ResponseFormat = responseFormatString switch
                        {
                            "text" => ChatResponseFormat.Text,
                            "json_object" => ChatResponseFormat.Json,
                            _ => null,
                        };
                    }
                    else
                    {
                        options.ResponseFormat = responseFormat is JsonElement e ? ChatResponseFormat.ForJsonSchema(e) : null;
                    }
                }
                else
                {
                    // Roundtripping a derived PromptExecutionSettings through the base type will have put all the
                    // object values in AdditionalProperties into JsonElements. Convert them back where possible.
                    object? value = entry.Value;
                    if (value is JsonElement jsonElement)
                    {
                        value = jsonElement.ValueKind switch
                        {
                            JsonValueKind.String => jsonElement.GetString(),
                            JsonValueKind.Number => jsonElement.GetDouble(), // not perfect, but a reasonable heuristic
                            JsonValueKind.True => true,
                            JsonValueKind.False => false,
                            JsonValueKind.Null => null,
                            _ => value,
                        };

                        if (jsonElement.ValueKind == JsonValueKind.Array)
                        {
                            var enumerator = jsonElement.EnumerateArray();

                            var enumeratorType = enumerator.MoveNext() ? enumerator.Current.ValueKind : JsonValueKind.Null;

                            switch (enumeratorType)
                            {
                                case JsonValueKind.String:
                                    value = enumerator.Select(e => e.GetString());
                                    break;
                                case JsonValueKind.Number:
                                    value = enumerator.Select(e => e.GetDouble());
                                    break;
                                case JsonValueKind.True or JsonValueKind.False:
                                    value = enumerator.Select(e => e.ValueKind == JsonValueKind.True);
                                    break;
                            }
                        }
                    }

                    (options.AdditionalProperties ??= [])[entry.Key] = value;
                }
            }
        }

        if (settings.FunctionChoiceBehavior?.GetConfiguration(new([]) { Kernel = kernel }).Functions is { Count: > 0 } functions)
        {
            options.ToolMode = settings.FunctionChoiceBehavior is RequiredFunctionChoiceBehavior ? ChatToolMode.RequireAny : ChatToolMode.Auto;
            options.Tools = functions.Select(f => f.AsAIFunction(kernel)).Cast<AITool>().ToList();
        }

        return options;

        // Be a little lenient on the types of the values used in the extension data,
        // e.g. allow doubles even when requesting floats.
        static bool TryConvert<T>(object? value, [NotNullWhen(true)] out T? result)
        {
            if (value is not null)
            {
                // If the value is a T, use it.
                if (value is T typedValue)
                {
                    result = typedValue;
                    return true;
                }

                if (value is JsonElement json)
                {
                    // If the value is JsonElement, it likely resulted from JSON serializing as object.
                    // Try to deserialize it as a T. This currently will only be successful either when
                    // reflection-based serialization is enabled or T is one of the types special-cased
                    // in the AbstractionsJsonContext. For other cases with NativeAOT, we would need to
                    // have a JsonSerializationOptions with the relevant type information.
                    if (AbstractionsJsonContext.TryGetTypeInfo(typeof(T), firstOptions: null, out JsonTypeInfo? jti))
                    {
                        try
                        {
                            result = (T)json.Deserialize(jti)!;
                            return true;
                        }
                        catch (Exception e) when (e is ArgumentException or JsonException or NotSupportedException or InvalidOperationException)
                        {
                        }
                    }
                }
                else
                {
                    // Otherwise, try to convert it to a T using Convert, in particular to handle conversions between numeric primitive types.
                    try
                    {
                        result = (T)Convert.ChangeType(value, typeof(T), CultureInfo.InvariantCulture);
                        return true;
                    }
                    catch (Exception e) when (e is ArgumentException or FormatException or InvalidCastException or OverflowException)
                    {
                    }
                }
            }

            result = default;
            return false;
        }
    }

    /// <summary>Converts a <see cref="ChatResponseUpdate"/> to a <see cref="StreamingChatMessageContent"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    private static StreamingChatMessageContent ToStreamingChatMessageContent(ChatResponseUpdate update)
    {
        StreamingChatMessageContent content = new(
            update.Role is not null ? new AuthorRole(update.Role.Value.Value) : null,
            null)
        {
            InnerContent = update.RawRepresentation,
            Metadata = update.AdditionalProperties,
            ModelId = update.ModelId
        };

        foreach (AIContent item in update.Contents)
        {
            StreamingKernelContent? resultContent =
                item is Microsoft.Extensions.AI.TextContent tc ? new Microsoft.SemanticKernel.StreamingTextContent(tc.Text) :
                item is Microsoft.Extensions.AI.FunctionCallContent fcc ?
                    new Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent(fcc.CallId, fcc.Name, fcc.Arguments is not null ?
                        JsonSerializer.Serialize(fcc.Arguments!, AbstractionsJsonContext.Default.IDictionaryStringObject!) :
                        null) :
                null;

            if (resultContent is not null)
            {
                resultContent.ModelId = update.ModelId;
                content.Items.Add(resultContent);
            }
        }

        return content;
    }
}
