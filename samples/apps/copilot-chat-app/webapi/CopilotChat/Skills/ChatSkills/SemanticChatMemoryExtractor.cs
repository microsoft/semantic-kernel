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
    /// <param name="memoryType">Name of the memory category</param>
    internal static string MemoryCollectionType(string chatId, string memoryType) => $"{chatId}-{memoryType}";

    /// <summary>
    /// Extract and save semantic memory.
    /// </summary>
    /// <param name="chatId">The Chat ID.</param>
    /// <param name="context">The SKContext</param>
    /// <param name="options">The prompts options.</param>
    /// <param name="chatPlugin">The plugin containing chat specific semantic functions as prompt templates.</param>
    /// <param name="chatPromptOptions">The token counts of the prompt text templates in the chatPlugin.</param>
    internal static async Task ExtractSemanticChatMemoryAsync(
        string chatId,
        SKContext context,
        PromptsOptions options,
        IDictionary<string, ISKFunction> chatPlugin,
        IDictionary<string, PluginPromptOptions> chatPluginPromptOptions)
    {
        var memoryExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        memoryExtractionContext.Variables.Set("MemoryFormat", options.MemoryFormat);

        foreach (var memoryType in options.MemoryTypes)
        {
            try
            {
                var memSkillName = "ExtractMemory" + memoryType;
                var semanticMemory = await ExtractCognitiveMemoryAsync(
                                            memoryType,
                                            memoryExtractionContext,
                                            options,
                                            chatPlugin[memSkillName],
                                            chatPluginPromptOptions[memSkillName]);

                foreach (var item in semanticMemory.Items)
                {
                    await CreateMemoryAsync(item, chatId, context, memoryType, options);
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Skip semantic memory extraction for this item if it fails.
                // We cannot rely on the model to response with perfect Json each time.
                context.Log.LogInformation("Unable to extract semantic memory for {0}: {1}. Continuing...", memoryType, ex.Message);
                continue;
            }
        }
    }

    /// <summary>
    /// Extracts the semantic chat memory from the chat session.
    /// </summary>
    /// <param name="memoryType">Name of the memory category</param>
    /// <param name="memoryExtractionContext">The SKContext</param>
    /// <param name="options">The prompts options.</param>
    /// <param name="extractMemoryFunc">The Semantic Function for memory extraction.</param>
    /// <param name="memoryPromptTokenCount">The token count used by the memory extraction prompt.txt template.</param>
    /// <returns>A SemanticChatMemory object.</returns>
    internal static async Task<SemanticChatMemory> ExtractCognitiveMemoryAsync(
        string memoryType,
        SKContext memoryExtractionContext,
        PromptsOptions options,
        ISKFunction extractMemoryFunc,
        PluginPromptOptions skillPromptOptions)
    {
        if (!options.MemoryTypes.Contains(memoryType))
        {
            throw new ArgumentException($"Memory type {memoryType} is not supported.");
        }

        // Token limit for chat history
        int maxTokens = skillPromptOptions.CompletionSettings.MaxTokens ?? 512;
        int remainingToken =
            options.CompletionTokenLimit -
            maxTokens -
            skillPromptOptions.PromptTokenCount;

        memoryExtractionContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));

        var result = await extractMemoryFunc.InvokeAsync(memoryExtractionContext, skillPromptOptions.CompletionSettings);

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
    /// <param name="memoryType">Name of the memory</param>
    /// <param name="options">The prompts options.</param>
    internal static async Task CreateMemoryAsync(
        SemanticChatMemoryItem item,
        string chatId,
        SKContext context,
        string memoryType,
        PromptsOptions options)
    {
        var memoryCollectionType = SemanticChatMemoryExtractor.MemoryCollectionType(chatId, memoryType);

        var memories = await context.Memory.SearchAsync(
                collection: memoryCollectionType,
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
                collection: memoryCollectionType,
                text: item.ToFormattedString(),
                id: Guid.NewGuid().ToString(),
                description: memoryType,
                cancellationToken: context.CancellationToken
            );
        }
    }
}
