// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI.ChatCompletion.TextWrapper;

public class ChatToTextConverter : IChatToTextConverter
{
    public const string IncomingMessageStart = "<|im_start|>";
    public const string IncomingMessageEnd = "<|im_end|>";
    private static readonly string UserIdentifier = $"[{AuthorRole.User.Label}]";
    private static readonly string AssistantIdentifier = $"[{AuthorRole.Assistant.Label}]";

    private static readonly string[] defaultStopSequences = new[] {
        IncomingMessageStart,
        IncomingMessageEnd,
        UserIdentifier,
        AssistantIdentifier };

    private sealed class ChatMessage : ChatMessageBase
    {
        public ChatMessage(AuthorRole authorRole, string content) : base(authorRole, content)
        {
        }
    }

    private sealed class ChatResultFromTextResult : IChatResult
    {
        private readonly ITextResult _textResults;

        public ChatResultFromTextResult(ITextResult textResults)
        {
            this._textResults = textResults;
        }

        public ModelResult ModelResult => this._textResults.ModelResult; // TODO return ChatModelResult

        public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        {
            string result = await this._textResults.GetCompletionAsync(cancellationToken).ConfigureAwait(false);

            return new ChatMessage(AuthorRole.Assistant, result);
        }
    }

    private sealed class ChatStreamingResultFromTextStreamingResult : IChatStreamingResult
    {
        private readonly ITextStreamingResult _textResults;

        public ChatStreamingResultFromTextStreamingResult(ITextStreamingResult textResults)
        {
            this._textResults = textResults;
        }

        public ModelResult ModelResult => this._textResults.ModelResult;

        public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        {
            string result = await this._textResults.GetCompletionAsync(cancellationToken).ConfigureAwait(false);
            return new ChatMessage(AuthorRole.Assistant, result);
        }

        public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await foreach (string? message in this._textResults.GetCompletionStreamingAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return new ChatMessage(AuthorRole.Assistant, message);
            }
        }
    }

    public CompleteRequestSettings ChatSettingsToCompleteSettings(ChatRequestSettings? textSettings)
    {
        var settings = textSettings == null ?
            new CompleteRequestSettings() :
            new CompleteRequestSettings()
            {
                Temperature = textSettings.Temperature,
                FrequencyPenalty = textSettings.FrequencyPenalty,
                MaxTokens = textSettings.MaxTokens,
                TopP = textSettings.TopP,
                PresencePenalty = textSettings.PresencePenalty,
                ResultsPerPrompt = textSettings.ResultsPerPrompt,
                TokenSelectionBiases = textSettings.TokenSelectionBiases
            };

        int numTextStopSequences = textSettings?.StopSequences?.Count ?? 0;
        var stopSequences = new List<string>(defaultStopSequences.Length + numTextStopSequences);

        stopSequences.AddRange(defaultStopSequences);
        if (numTextStopSequences > 0)
        {
            stopSequences.AddRange(textSettings.StopSequences);
        }

        settings.StopSequences = stopSequences;

        return settings;
    }

    public string ChatToText(ChatHistory chat)
    {
        var sb = new StringBuilder();

        foreach (ChatMessageBase message in chat.Messages)
        {
            WriteRolePrefix(sb, message.Role);

            sb.Append(message.Content);

            sb.Append($"{IncomingMessageEnd}\n");
        }

        WriteRolePrefix(sb, AuthorRole.Assistant);

        return sb.ToString();
    }

    private static void WriteRolePrefix(StringBuilder sb, AuthorRole role)
    {
        if (role != AuthorRole.System)
        {
            sb.Append($"{IncomingMessageStart}[{role}]\n");
        }
    }

    public IReadOnlyList<IChatResult> TextResultToChatResult(IReadOnlyList<ITextResult> result)
    {
        if (result.Count == 0)
        {
            return Array.Empty<IChatResult>();
        }

        var chatResults = new List<IChatResult>(result.Count);
        for (int i = 0; i < result.Count; i++)
        {
            chatResults.Add(new ChatResultFromTextResult(result[i]));
        }

        return chatResults;
    }

    public async IAsyncEnumerable<IChatStreamingResult> TextStreamingResultToChatStreamingResult(IAsyncEnumerable<ITextStreamingResult> result)
    {
        await foreach (ITextStreamingResult textResult in result)
        {
            yield return new ChatStreamingResultFromTextStreamingResult(textResult);
        }
    }
}
