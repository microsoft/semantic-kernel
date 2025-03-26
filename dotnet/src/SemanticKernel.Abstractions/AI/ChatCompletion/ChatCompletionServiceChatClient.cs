// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides an implementation of <see cref="IChatClient"/> around an arbitrary <see cref="IChatCompletionService"/>.</summary>
internal sealed class ChatCompletionServiceChatClient : IChatClient
{
    /// <summary>The wrapped <see cref="IChatCompletionService"/>.</summary>
    private readonly IChatCompletionService _chatCompletionService;

    /// <summary>Initializes the <see cref="ChatCompletionServiceChatClient"/> for <paramref name="chatCompletionService"/>.</summary>
    public ChatCompletionServiceChatClient(IChatCompletionService chatCompletionService)
    {
        Verify.NotNull(chatCompletionService);

        this._chatCompletionService = chatCompletionService;

        this.Metadata = new ChatClientMetadata(
            chatCompletionService.GetType().Name,
            chatCompletionService.GetEndpoint() is string endpoint ? new Uri(endpoint) : null,
            chatCompletionService.GetModelId());
    }

    /// <inheritdoc />
    public ChatClientMetadata Metadata { get; }

    /// <inheritdoc />
    public async Task<Extensions.AI.ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        ChatHistory chatHistory = new(messages.Select(m => ChatCompletionServiceExtensions.ToChatMessageContent(m)));
        int preCount = chatHistory.Count;

        var response = await this._chatCompletionService.GetChatMessageContentAsync(
            chatHistory,
            ToPromptExecutionSettings(options),
            kernel: null,
            cancellationToken).ConfigureAwait(false);

        ChatResponse chatResponse = new()
        {
            ModelId = response.ModelId,
            RawRepresentation = response.InnerContent,
        };

        // Add all messages that were added to the history.
        // Then add the result message.
        for (int i = preCount; i < chatHistory.Count; i++)
        {
            chatResponse.Messages.Add(ChatCompletionServiceExtensions.ToChatMessage(chatHistory[i]));
        }

        chatResponse.Messages.Add(ChatCompletionServiceExtensions.ToChatMessage(response));

        return chatResponse;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        await foreach (var update in this._chatCompletionService.GetStreamingChatMessageContentsAsync(
            new ChatHistory(messages.Select(m => ChatCompletionServiceExtensions.ToChatMessageContent(m))),
            ToPromptExecutionSettings(options),
            kernel: null,
            cancellationToken).ConfigureAwait(false))
        {
            yield return ToStreamingChatCompletionUpdate(update);
        }
    }

    /// <inheritdoc />
    public void Dispose()
    {
        (this._chatCompletionService as IDisposable)?.Dispose();
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            serviceType.IsInstanceOfType(this._chatCompletionService) ? this._chatCompletionService :
            serviceType.IsInstanceOfType(this.Metadata) ? this.Metadata :
            null;
    }

    /// <summary>Converts a <see cref="ChatOptions"/> to a <see cref="PromptExecutionSettings"/>.</summary>
    private static PromptExecutionSettings? ToPromptExecutionSettings(ChatOptions? options)
    {
        if (options is null)
        {
            return null;
        }

        PromptExecutionSettings settings = new()
        {
            ExtensionData = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase),
            ModelId = options.ModelId,
        };

        // Transfer over all strongly-typed members of ChatOptions. We do not know the exact name the derived PromptExecutionSettings
        // will pick for these options, so we just use the most common choice for each. (We could make this more exact by having an
        // IPromptExecutionSettingsFactory interface with a method like `PromptExecutionSettings Create(ChatOptions options)`; that
        // interface could then optionally be implemented by an IChatCompletionService, and this implementation could just ask the
        // chat completion service to produce the PromptExecutionSettings it wants. But, this is already a problem
        // with PromptExecutionSettings, regardless of ChatOptions... someone creating a PES without knowing what backend is being
        // used has to guess at the names to use.)

        if (options.Temperature is not null)
        {
            settings.ExtensionData["temperature"] = options.Temperature.Value;
        }

        if (options.MaxOutputTokens is not null)
        {
            settings.ExtensionData["max_tokens"] = options.MaxOutputTokens.Value;
        }

        if (options.FrequencyPenalty is not null)
        {
            settings.ExtensionData["frequency_penalty"] = options.FrequencyPenalty.Value;
        }

        if (options.PresencePenalty is not null)
        {
            settings.ExtensionData["presence_penalty"] = options.PresencePenalty.Value;
        }

        if (options.StopSequences is not null)
        {
            settings.ExtensionData["stop_sequences"] = options.StopSequences;
        }

        if (options.TopP is not null)
        {
            settings.ExtensionData["top_p"] = options.TopP.Value;
        }

        if (options.TopK is not null)
        {
            settings.ExtensionData["top_k"] = options.TopK.Value;
        }

        if (options.Seed is not null)
        {
            settings.ExtensionData["seed"] = options.Seed.Value;
        }

        if (options.ResponseFormat is not null)
        {
            if (options.ResponseFormat is ChatResponseFormatText)
            {
                settings.ExtensionData["response_format"] = "text";
            }
            else if (options.ResponseFormat is ChatResponseFormatJson json)
            {
                settings.ExtensionData["response_format"] = json.Schema is JsonElement schema ?
                    JsonSerializer.Deserialize(schema, AbstractionsJsonContext.Default.JsonElement) :
                    "json_object";
            }
        }

        // Transfer over loosely-typed members of ChatOptions.

        if (options.AdditionalProperties is not null)
        {
            foreach (var kvp in options.AdditionalProperties)
            {
                if (kvp.Value is not null)
                {
                    settings.ExtensionData[kvp.Key] = kvp.Value;
                }
            }
        }

        // Transfer over tools. For IChatClient, we do not want automatic invocation, as that's a concern left up to
        // components like FunctionInvocationChatClient. As such, based on the tool mode, we map to the appropriate
        // FunctionChoiceBehavior, but always with autoInvoke: false.

        if (options.Tools is { Count: > 0 })
        {
            var functions = options.Tools.OfType<AIFunction>().Select(aiFunction => aiFunction.AsKernelFunction());
            settings.FunctionChoiceBehavior =
                options.ToolMode is null or AutoChatToolMode ? FunctionChoiceBehavior.Auto(functions, autoInvoke: false) :
                options.ToolMode is RequiredChatToolMode { RequiredFunctionName: null } ? FunctionChoiceBehavior.Required(functions, autoInvoke: false) :
                options.ToolMode is RequiredChatToolMode { RequiredFunctionName: string functionName } ? FunctionChoiceBehavior.Required(functions.Where(f => f.Name == functionName), autoInvoke: false) :
                null;
        }

        return settings;
    }

    /// <summary>Converts a <see cref="StreamingChatMessageContent"/> to a <see cref="ChatResponseUpdate"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    private static ChatResponseUpdate ToStreamingChatCompletionUpdate(StreamingChatMessageContent content)
    {
        ChatResponseUpdate update = new()
        {
            AdditionalProperties = content.Metadata is not null ? new AdditionalPropertiesDictionary(content.Metadata) : null,
            AuthorName = content.AuthorName,
            ModelId = content.ModelId,
            RawRepresentation = content,
            Role = content.Role is not null ? new ChatRole(content.Role.Value.Label) : null,
        };

        foreach (var item in content.Items)
        {
            AIContent? aiContent = null;
            switch (item)
            {
                case Microsoft.SemanticKernel.StreamingTextContent tc:
                    aiContent = new Microsoft.Extensions.AI.TextContent(tc.Text);
                    break;

                case Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent fcc:
                    aiContent = new Microsoft.Extensions.AI.FunctionCallContent(
                        fcc.CallId ?? string.Empty,
                        fcc.Name ?? string.Empty,
                        fcc.Arguments is not null ? JsonSerializer.Deserialize<IDictionary<string, object?>>(fcc.Arguments, AbstractionsJsonContext.Default.IDictionaryStringObject!) : null);
                    break;
            }

            if (aiContent is not null)
            {
                aiContent.RawRepresentation = content;

                update.Contents.Add(aiContent);
            }
        }

        return update;
    }
}
