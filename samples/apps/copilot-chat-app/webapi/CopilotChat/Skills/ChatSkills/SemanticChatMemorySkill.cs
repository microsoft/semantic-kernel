// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
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
    [SKFunction("Query chat memories")]
    [SKFunctionName("QueryMemories")]
    [SKFunctionInput(Description = "Query to match.")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to query history from")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> QueryMemoriesAsync(string query, SKContext context)
    {
        var chatId = context["chatId"];
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var remainingToken = tokenLimit;

        // Search for relevant memories.
        List<MemoryQueryResult> relevantMemories = new();
        foreach (var memoryName in this._promptOptions.MemoryMap.Keys)
        {
            var results = context.Memory.SearchAsync(
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
