// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.CopilotChat.Extensions;
using SemanticKernel.Service.CopilotChat.Options;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

/// <summary>
/// Helper class to extract and create semantic memory from chat history.
/// </summary>
internal static class SemanticChatMemoryExtractor
{
    /// <summary>
    /// Returns the name of the semantic text memory collection that stores chat semantic memory.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique for the chat session.</param>
    /// <param name="memoryName">Name of the memory category</param>
    internal static string MemoryCollectionName(string chatId, string memoryName) => $"{chatId}-{memoryName}";

    /// <summary>
    /// Extract and save semantic memory.
    /// </summary>
    /// <param name="chatId">The Chat ID.</param>
    /// <param name="kernel">The semantic kernel.</param>
    /// <param name="context">The context containing the memory.</param>
    /// <param name="options">The prompts options.</param>
    internal static async Task ExtractSemanticChatMemoryAsync(
        string chatId,
        SKContext context,
        PromptsOptions options,
        IDictionary<string, ISKFunction> chatSkillPlugin,
        IDictionary<string, int> chatSkillTokenCounts)
    {
        var memoryExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        memoryExtractionContext.Variables.Set("format", options.MemoryFormat);

        foreach (var memoryName in options.MemoryTypes)
        {
            try
            {
                var memSkillName = "ExtractMemory" + memoryName;
                var semanticMemory = await ExtractCognitiveMemoryAsync(
                                            memoryName,
                                            memoryExtractionContext,
                                            options,
                                            chatSkillPlugin[memSkillName],
                                            chatSkillTokenCounts[memSkillName]);

                foreach (var item in semanticMemory.Items)
                {
                    await CreateMemoryAsync(item, chatId, context, memoryName, options);
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Skip semantic memory extraction for this item if it fails.
                // We cannot rely on the model to response with perfect Json each time.
                context.Log.LogInformation("Unable to extract semantic memory for {0}: {1}. Continuing...", memoryName, ex.Message);
                continue;
            }
        }
    }

    /// <summary>
    /// Extracts the semantic chat memory from the chat session.
    /// </summary>
    /// <param name="memoryName">Name of the memory category</param>
    /// <param name="context">The SKContext</param>
    /// <param name="options">The prompts options.</param>
    /// <returns>A SemanticChatMemory object.</returns>
    internal static async Task<SemanticChatMemory> ExtractCognitiveMemoryAsync(
        string memoryName,
        SKContext memoryExtractionContext,
        PromptsOptions options,
        ISKFunction extractMemorySKFunc,
        int memoryPromptTokenCount)
    {
        if (!options.MemoryTypes.Contains(memoryName))
        {
            throw new ArgumentException($"Memory name {memoryName} is not supported.");
        }

        // Token limit for chat history
        var remainingToken =
            options.CompletionTokenLimit -
            options.ResponseTokenLimit -
            memoryPromptTokenCount;

        memoryExtractionContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));

        var result = await extractMemorySKFunc.InvokeAsync(memoryExtractionContext);

        SemanticChatMemory memory = SemanticChatMemory.FromJson(result.ToString());
        return memory;
    }

    /// <summary>
    /// Create a memory item in the memory collection.
    /// If there is already a memory item that has a high similarity score with the new item, it will be skipped.
    /// </summary>
    /// <param name="item">A SemanticChatMemoryItem instance</param>
    /// <param name="chatId">The ID of the chat the memories belong to</param>
    /// <param name="context">The context that contains the memory</param>
    /// <param name="memoryName">Name of the memory</param>
    /// <param name="options">The prompts options.</param>
    internal static async Task CreateMemoryAsync(
        SemanticChatMemoryItem item,
        string chatId,
        SKContext context,
        string memoryName,
        PromptsOptions options)
    {
        var memoryCollectionName = SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName);

        var memories = await context.Memory.SearchAsync(
                collection: memoryCollectionName,
                query: item.ToFormattedString(),
                limit: 1,
                minRelevanceScore: options.SemanticMemoryMinRelevance,
                cancellationToken: context.CancellationToken
            )
            .ToListAsync()
            .ConfigureAwait(false);

        if (memories.Count == 0)
        {
            await context.Memory.SaveInformationAsync(
                collection: memoryCollectionName,
                text: item.ToFormattedString(),
                id: Guid.NewGuid().ToString(),
                description: memoryName,
                cancellationToken: context.CancellationToken
            );
        }
    }
}
