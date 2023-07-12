// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.CopilotChat.Options;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

/// <summary>
/// This skill provides the functions to query the semantic chat memory.
/// </summary>
public class SemanticChatMemorySkill
{
    /// <summary>
    /// Prompt settings.
    /// </summary>
    private readonly PromptsOptions _promptOptions;

    /// <summary>
    /// Create a new instance of SemanticChatMemorySkill.
    /// </summary>
    public SemanticChatMemorySkill(
        IOptions<PromptsOptions> promptOptions)
    {
        this._promptOptions = promptOptions.Value;
    }

    /// <summary>
    /// Query relevant memories based on the query.
    /// </summary>
    /// <param name="query">Query to match.</param>
    /// <param name="context">The SKContext</param>
    /// <returns>A string containing the relevant memories.</returns>
    [SKFunction, Description("Query chat memories")]
    public async Task<string> QueryMemoriesAsync(
        [Description("Query to match.")] string query,
        [Description("Chat ID to query history from")] string chatId,
        [Description("Maximum number of tokens")] int tokenLimit,
        ISemanticTextMemory textMemory)
    {
        var remainingToken = tokenLimit;

        // Search for relevant memories.
        List<MemoryQueryResult> relevantMemories = new();
        foreach (var memoryName in this._promptOptions.MemoryMap.Keys)
        {
            var results = textMemory.SearchAsync(
                SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName),
                query,
                limit: 100,
                minRelevanceScore: this._promptOptions.SemanticMemoryMinRelevance);
            await foreach (var memory in results)
            {
                relevantMemories.Add(memory);
            }
        }

        relevantMemories = relevantMemories.OrderByDescending(m => m.Relevance).ToList();

        string memoryText = "";
        foreach (var memory in relevantMemories)
        {
            var tokenCount = Utilities.TokenCount(memory.Metadata.Text);
            if (remainingToken - tokenCount > 0)
            {
                memoryText += $"\n[{memory.Metadata.Description}] {memory.Metadata.Text}";
                remainingToken -= tokenCount;
            }
            else
            {
                break;
            }
        }

        if (string.IsNullOrEmpty(memoryText))
        {
            // No relevant memories found
            return string.Empty;
        }

        return $"Past memories (format: [memory type] <label>: <details>):\n{memoryText.Trim()}";
    }
}
