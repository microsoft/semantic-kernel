using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Service.Skills;

/// <summary>
///
/// </summary>
internal class SemanticMemoryExtractor
{
    /// <summary>
    /// Returns the name of the semantic text memory collection that stores chat semantic memory.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique for the chat session.</param>
    /// <param name="memoryName">Name of the memory category</param>
    internal static string MemoryCollectionName(string chatId, string memoryName) => $"{chatId}-{memoryName}";

    internal static async Task<SemanticChatMemory> ExtractCognitiveMemoryAsync(string memoryName, IKernel kernel, SKContext context)
    {
        if (!SystemPromptDefaults.MemoryMap.TryGetValue(memoryName, out var memoryPrompt))
        {
            throw new ArgumentException($"Memory name {memoryName} is not supported.");
        }

        var tokenLimit = SystemPromptDefaults.CompletionTokenLimit;
        var remainingToken = tokenLimit - SystemPromptDefaults.ResponseTokenLimit;
        var contextTokenLimit = remainingToken;

        var memoryExtractionContext = Utils.CopyContextWithVariablesClone(context);
        memoryExtractionContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
        memoryExtractionContext.Variables.Set("memoryName", memoryName);
        memoryExtractionContext.Variables.Set("format", SystemPromptDefaults.MemoryFormat);
        memoryExtractionContext.Variables.Set("knowledgeCutoff", SystemPromptDefaults.KnowledgeCutoffDate);

        var completionFunction = kernel.CreateSemanticFunction(memoryPrompt);
        var result = await completionFunction.InvokeAsync(
            context: memoryExtractionContext,
            settings: CreateMemoryExtractionSettings()
        );

        SemanticChatMemory memory = SemanticChatMemory.FromJson(result.ToString());
        return memory;
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the SystemPromptDefaults class.
    /// </summary>
    private static CompleteRequestSettings CreateMemoryExtractionSettings()
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = SystemPromptDefaults.ResponseTokenLimit,
            Temperature = SystemPromptDefaults.ResponseTemperature,
            TopP = SystemPromptDefaults.ResponseTopP,
            FrequencyPenalty = SystemPromptDefaults.ResponseFrequencyPenalty,
            PresencePenalty = SystemPromptDefaults.ResponsePresencePenalty
        };

        return completionSettings;
    }
}
