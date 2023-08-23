// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Extensions;

using Models;
using SemanticKernel.AI.ChatCompletion;


internal static class SourceGraphRequestExtensions
{
    public static CompletionsInput Create(this CompletionsInput completionsInput, ChatHistory chatHistory, ChatRequestSettings? requestSettings = null)
    {
        completionsInput.Messages = chatHistory.Messages
            .Select(Message.FromChatMessageBase).ToList();

        completionsInput.MaxTokensToSample = requestSettings?.MaxTokens ?? 2048;
        completionsInput.Temperature = requestSettings?.Temperature ?? 0.0;
        completionsInput.TopP = (int)(requestSettings?.TopP ?? 1);
        completionsInput.TopK = 1;
        return completionsInput;
    }


    public static CompletionsRequest Create(this CompletionsRequest completionsInput, ChatHistory chatHistory, ChatRequestSettings? requestSettings = null)
    {
        completionsInput.Messages = chatHistory.Messages
            .Select(Message.FromChatMessageBase).ToArray();

        completionsInput.MaxTokens = requestSettings?.MaxTokens ?? 2048;
        completionsInput.Temperature = (float)(requestSettings?.Temperature ?? 0.0);
        completionsInput.TopP = (int)(requestSettings?.TopP ?? 1);
        completionsInput.StopSequences = requestSettings?.StopSequences.ToArray();
        completionsInput.PresencePenalty = (int)(requestSettings?.PresencePenalty ?? 0.0);
        completionsInput.FrequencyPenalty = (int)(requestSettings?.FrequencyPenalty ?? 0.0);
        return completionsInput;
    }
}
