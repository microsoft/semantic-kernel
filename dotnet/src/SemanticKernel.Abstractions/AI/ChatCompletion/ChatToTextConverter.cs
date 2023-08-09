// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public class ChatToTextConverter : IChatToTextConverter
{
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


            if (message.Role is  userMessage)
            {
                sb.AppendLine(userMessage.Text);
            }
            else if (message is SystemMessage systemMessage)
            {
                sb.AppendLine(systemMessage.Text);
            }
            else
            {
                throw new NotSupportedException($"Message type {message.GetType().Name} is not supported");
            }
        }
        return sb.ToString();
    }

    public IReadOnlyList<IChatResult> TextResultToChatResult(IReadOnlyList<ITextResult> result)
    {

    }

    public IAsyncEnumerable<IChatStreamingResult> TextResultToChatResult(IAsyncEnumerable<ITextStreamingResult> result)
    {

    }
}
