// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
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

    public CompleteRequestSettings ChatSettingsToCompleteSettings(ChatRequestSettings? textSettings)
    {
        var settings = textSettings == null ?
            new CompleteRequestSettings() :
            new CompleteRequestSettings()
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

        // TODO HACK
        //settings.StopSequences = new List<string>() { "USER", "\nASSISTANT" };
        //settings.StopSequences = new List<string>() { "<im_start>" };
        settings.StopSequences = new List<string>() {
                "<|im_end|>",
                "<|im_start|>",
                "[assistant]",
                "[user]"
            };
        settings.MaxTokens ??= 200;

        return settings;
    }

    public string ChatToText(ChatHistory chat)
    {
        var sb = new StringBuilder();

        foreach (ChatMessageBase message in chat.Messages)
        {
            WriteRolePrefix(sb, message.Role);

            sb.Append(message.Content);
            sb.Append("<|im_end|>\n");
        }

        WriteRolePrefix(sb, AuthorRole.Assistant);

        return sb.ToString();
    }

    private static void WriteRolePrefix(StringBuilder sb, AuthorRole role)
    {
        if (role != AuthorRole.System)
        {
            sb.Append("<|im_start|>[");
            sb.Append(role);
            sb.Append("]\n");
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

    public IAsyncEnumerable<IChatStreamingResult> TextStreamingResultToChatStreamingResult(IAsyncEnumerable<ITextStreamingResult> result)
    {
        throw new NotImplementedException("Streaming is currently not supported in the ChatToText converter");
        /*await foreach (ITextStreamingResult message in result)
        {
            yield return new ChatStreamingResultFromTextStreamingResult(message);
        }*/
    }
}
