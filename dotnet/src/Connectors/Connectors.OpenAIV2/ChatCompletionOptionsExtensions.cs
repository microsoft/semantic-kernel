// Copyright (c) Microsoft. All rights reserved.

using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal static class ChatCompletionOptionsExtensions
{
    internal static ChatCompletionOptions CloneWith(this ChatCompletionOptions options, ChatToolChoice choice)
    {
        var newOptions = new ChatCompletionOptions
        {
            MaxTokens = options.MaxTokens,
            Temperature = options.Temperature,
            TopP = options.TopP,
            PresencePenalty = options.PresencePenalty,
            FrequencyPenalty = options.FrequencyPenalty,
            FunctionChoice = options.FunctionChoice,
            ResponseFormat = options.ResponseFormat,
            IncludeLogProbabilities = options.IncludeLogProbabilities,
            Seed = options.Seed,
            User = options.User,
            ToolChoice = choice,
            TopLogProbabilityCount = options.TopLogProbabilityCount,
        };

        if (options.Functions.Count > 0)
        {
            newOptions.Functions.AddRange(options.Functions);
        }

        if (options.Tools.Count > 0)
        {
            newOptions.Tools.AddRange(options.Tools);
        }

        if (options.StopSequences.Count > 0)
        {
            newOptions.StopSequences.AddRange(options.StopSequences);
        }

        return newOptions;
    }
}
