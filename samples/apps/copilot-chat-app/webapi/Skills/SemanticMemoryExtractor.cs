// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Service.Skills;

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
        PromptSettings promptSettings)
    {
        if (!promptSettings.MemoryMap.TryGetValue(memoryName, out var memoryPrompt))
        {
            throw new ArgumentException($"Memory name {memoryName} is not supported.");
        }

        var tokenLimit = promptSettings.CompletionTokenLimit;
        var remainingToken = tokenLimit - promptSettings.ResponseTokenLimit;
        var contextTokenLimit = remainingToken;

        var memoryExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        memoryExtractionContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("memoryName", memoryName);
        memoryExtractionContext.Variables.Set("format", promptSettings.MemoryFormat);
        memoryExtractionContext.Variables.Set("knowledgeCutoff", promptSettings.KnowledgeCutoffDate);

        var completionFunction = kernel.CreateSemanticFunction(memoryPrompt);
        var result = await completionFunction.InvokeAsync(
            context: memoryExtractionContext,
            settings: CreateMemoryExtractionSettings(promptSettings)
        );

        SemanticChatMemory memory = SemanticChatMemory.FromJson(result.ToString());
        return memory;
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the PromptSettings class.
    /// </summary>
    private static JsonObject CreateMemoryExtractionSettings(PromptSettings promptSettings)
    {
        var completionSettings = new JsonObject
        {
            ["max_tokens"] = promptSettings.ResponseTokenLimit,
            ["temperature"] = promptSettings.ResponseTemperature,
            ["top_p"] = promptSettings.ResponseTopP,
            ["frequency_penalty"] = promptSettings.ResponseFrequencyPenalty,
            ["presence_penalty"] = promptSettings.ResponsePresencePenalty
        };

        return completionSettings;
    }
}
