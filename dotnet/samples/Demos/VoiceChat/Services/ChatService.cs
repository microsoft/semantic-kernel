// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

public class ChatService
{
    private readonly ILogger<ChatService> _logger;
    private readonly IChatCompletionService _chatCompletionService;
    private readonly ChatHistory _chatHistory;
    private readonly OpenAIPromptExecutionSettings _options;
    private readonly ChatOptions _chatOptions;

    public ChatService(ILogger<ChatService> logger, IChatCompletionService chatCompletionService, IOptions<ChatOptions> chatOptions)
    {
        this._logger = logger;
        this._chatCompletionService = chatCompletionService;
        this._chatOptions = chatOptions.Value;

        this._options = new OpenAIPromptExecutionSettings
        {
            Temperature = this._chatOptions.Temperature,
            MaxTokens = this._chatOptions.MaxTokens,
            TopP = this._chatOptions.TopP
        };

        // Initialize chat history with system message from configuration
        this._chatHistory = new ChatHistory();
        this._chatHistory.AddSystemMessage(this._chatOptions.SystemMessage);
    }

    /// <summary>
    /// Pipeline integration method for processing transcription events into chat responses.
    /// </summary>
    public async IAsyncEnumerable<ChatEvent> TransformAsync(TranscriptionEvent evt)
    {
        await foreach (var response in this.GetResponseStreamAsync(evt.Payload!, evt.CancellationToken).ConfigureAwait(false))
        {
            yield return new ChatEvent(evt.TurnId, evt.CancellationToken, response);
        }
    }

    private async IAsyncEnumerable<string> GetResponseStreamAsync(
        string input,
        [EnumeratorCancellation] CancellationToken token = default)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            yield break;
        }

        var buffer = "";
        this._logger.LogInformation($"USER: {input}");
        this._chatHistory.AddUserMessage(input);

        await foreach (var result in this._chatCompletionService.GetStreamingChatMessageContentsAsync(this._chatHistory, this._options, cancellationToken: token))
        {
            buffer += result?.Content ?? string.Empty;
            if (buffer.Length >= this._chatOptions.StreamingChunkSizeThreshold && (buffer[^1] == '.' || buffer[^1] == '?' || buffer[^1] == '!'))
            {
                this._logger.LogInformation($"LLM delta: {buffer}");
                yield return buffer;
                buffer = string.Empty;
            }
        }

        if (!string.IsNullOrWhiteSpace(buffer))
        {
            this._logger.LogInformation($"LLM delta: {buffer}");
            yield return buffer;
        }
    }
}
