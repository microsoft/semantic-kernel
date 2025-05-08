// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Transforms;

/// <summary>
/// Populates the target result type  <see cref="ChatMessageContent"/> into a structured output.
/// </summary>
/// <typeparam name="TOutput">The type of the structured output to deserialize to.</typeparam>
public sealed class StructuredOutputTransform<TOutput>
{
    internal const string DefaultInstructions = "Please respond with a JSON object that contains the.";

    private readonly IChatCompletionService _service;
    private readonly PromptExecutionSettings _executionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="StructuredOutputTransform{TOutput}"/> class.
    /// </summary>
    /// <param name="service">The chat completion service to use for generating responses.</param>
    /// <param name="executionSettings">The prompt execution settings to use for the chat completion service.</param>
    public StructuredOutputTransform(IChatCompletionService service, PromptExecutionSettings executionSettings)
    {
        Verify.NotNull(service, nameof(service));
        Verify.NotNull(executionSettings, nameof(executionSettings));

        this._service = service;
        this._executionSettings = executionSettings;
    }

    /// <summary>
    /// Gets or sets the instructions to be used as the system message for the chat completion.
    /// </summary>
    public string Instructions { get; init; } = DefaultInstructions;

    /// <summary>
    /// Transforms the provided <see cref="ChatMessageContent"/> into a strongly-typed structured output by invoking the chat completion service and deserializing the response.
    /// </summary>
    /// <param name="message">The chat message content to process.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>The structured output of type <typeparamref name="TOutput"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the response cannot be deserialized into <typeparamref name="TOutput"/>.</exception>
    public async ValueTask<TOutput> TransformAsync(ChatMessageContent message, CancellationToken cancellationToken = default)
    {
        ChatHistory history =
            [
                new ChatMessageContent(AuthorRole.System, this.Instructions),
                message,
            ];
        ChatMessageContent response = await this._service.GetChatMessageContentAsync(history, this._executionSettings, kernel: null, cancellationToken).ConfigureAwait(false);
        return
            JsonSerializer.Deserialize<TOutput>(response.Content ?? string.Empty) ??
            throw new InvalidOperationException($"Unable to transform result into {typeof(TOutput).Name}");
    }
}
