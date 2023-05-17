// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.Service.CopilotChat.Config;

namespace SemanticKernel.Service.CopilotChat.Skills;

internal static class SemanticMemoryExtractor
{
    /// <summary>
    /// Returns the name of the semantic text memory collection that stores chat semantic memory.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique for the chat session.</param>
    /// <param name="memoryName">Name of the memory category</param>
    internal static string MemoryCollectionName(string chatId, string memoryName) => $"{chatId}-{memoryName}";

    internal static async Task<SemanticChatMemory> ExtractCognitiveMemoryAsync(
        string memoryName,
        IKernel kernel,
        SKContext context,
        PromptsOptions options)
    {
        if (!options.MemoryMap.TryGetValue(memoryName, out var memoryPrompt))
        {
            throw new ArgumentException($"Memory name {memoryName} is not supported.");
        }

        var tokenLimit = options.CompletionTokenLimit;
        var remainingToken = tokenLimit - options.ResponseTokenLimit;
        var contextTokenLimit = remainingToken;

        var memoryExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        memoryExtractionContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("memoryName", memoryName);
        memoryExtractionContext.Variables.Set("format", options.MemoryFormat);
        memoryExtractionContext.Variables.Set("knowledgeCutoff", options.KnowledgeCutoffDate);

        var completionFunction = kernel.CreateSemanticFunction(memoryPrompt);
        var result = await completionFunction.InvokeAsync(
            context: memoryExtractionContext,
            settings: CreateMemoryExtractionSettings(options)
        );

        SemanticChatMemory memory = SemanticChatMemory.FromJson(result.ToString());
        return memory;
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the PromptSettings class.
    /// </summary>
    private static CompleteRequestSettings CreateMemoryExtractionSettings(PromptsOptions options)
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = options.ResponseTokenLimit,
            Temperature = options.ResponseTemperature,
            TopP = options.ResponseTopP,
            FrequencyPenalty = options.ResponseFrequencyPenalty,
            PresencePenalty = options.ResponsePresencePenalty
        };

        return completionSettings;
    }
}
