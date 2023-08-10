// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public class ChatToTextConverter : IChatToTextConverter
{
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

        public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        {
            string result = await this._textResults.GetCompletionAsync(cancellationToken).ConfigureAwait(false);
            return new ChatMessage(AuthorRole.Assistant, result);
        }
    }

    /*private sealed class ChatStreamingResultFromTextStreamingResult : IChatStreamingResult
    {
        private readonly ITextStreamingResult _textResults;

        public ChatStreamingResultFromTextStreamingResult(ITextStreamingResult textResults)
        {
            this._textResults = textResults;
        }

        public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        {
            string result = await this._textResults.GetCompletionAsync(cancellationToken).ConfigureAwait(false);
            return new ChatMessage(AuthorRole.Assistant, result);
        }

        public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync(CancellationToken cancellationToken = default)
        {
            // TODO actually stream
            yield return await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        }
    }*/

    public CompleteRequestSettings? ChatSettingsToCompleteSettings(ChatRequestSettings? textSettings)
    {
        if (textSettings == null)
        {
            return null;
        }

        return new CompleteRequestSettings()
        {
            Temperature = textSettings.Temperature,
            FrequencyPenalty = textSettings.FrequencyPenalty,
            MaxTokens = textSettings.MaxTokens,
            StopSequences = textSettings.StopSequences,
            TopP = textSettings.TopP,
            PresencePenalty = textSettings.PresencePenalty,
            ResultsPerPrompt = textSettings.ResultsPerPrompt,
            TokenSelectionBiases = textSettings.TokenSelectionBiases
        };
    }

    public string ChatToText(ChatHistory chat)
    {
        var sb = new StringBuilder();

        foreach (ChatMessageBase message in chat.Messages)
        {
            sb.AppendLine(message.Role + ": " + message.Content);
        }
        return sb.ToString();
    }

    public IReadOnlyList<IChatResult> TextResultToChatResult(IReadOnlyList<ITextResult> result)
    {
        var chatResults = new List<IChatResult>(result.Count);
        for (int i = 0; i < result.Count; i++)
        {
            chatResults[i] = new ChatResultFromTextResult(result[i]);
        }

        return chatResults;
    }

    public IAsyncEnumerable<IChatStreamingResult> TextStreamingResultToChatStreamingResult(IAsyncEnumerable<ITextStreamingResult> result)
    {
        throw new NotImplementedException("Streaming is currently not supported in the ChatToText converter");
        /*await foreach (ITextStreamingResult message in result)
        {
            yield return new ChatStreamingResultFromTextStreamingResult(message);
        }*/
    }
}
