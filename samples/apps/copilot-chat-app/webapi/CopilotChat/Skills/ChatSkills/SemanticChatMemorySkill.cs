// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

/// <summary>
/// This skill provides the functions to query the semantic chat memory.
/// </summary>
public class SemanticChatMemorySkill
{
    private readonly PromptsOptions _promptOptions;

    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Create a new instance of SemanticChatMemorySkill.
    /// </summary>
    public SemanticChatMemorySkill(
        IOptions<PromptsOptions> promptOptions,
        ChatSessionRepository chatSessionRepository)
    {
        this._promptOptions = promptOptions.Value;
        this._chatSessionRepository = chatSessionRepository;
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
        ChatSession? chatSession = null;
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId, v => chatSession = v))
        {
            throw new ArgumentException($"Chat session {chatId} not found.");
        }

        var remainingToken = tokenLimit;

        // Search for relevant memories.
        List<MemoryQueryResult> relevantMemories = new();
        foreach (var memoryName in this._promptOptions.MemoryMap.Keys)
        {
            var results = textMemory.SearchAsync(
                SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName),
                query,
                limit: 100,
                minRelevanceScore: this.CalculateRelevanceThreshold(memoryName, chatSession!.MemoryBalance));
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

    #region Private

    /// <summary>
    /// Calculates the relevance threshold for the memory.
    /// </summary>
    /// <param name="memoryName">The name of the memory.</param>
    /// <param name="memoryBalance">The balance between long term memory and working term memory.</param>
    /// <returns></returns>
    /// <exception cref="ArgumentException">Thrown when the memory name is invalid.</exception>
    private double CalculateRelevanceThreshold(string memoryName, double memoryBalance)
    {
        var upper = this._promptOptions.SemanticMemoryRelevanceUpper;
        var lower = this._promptOptions.SemanticMemoryRelevanceLower;

        if (memoryName == this._promptOptions.LongTermMemoryName)
        {
            return (lower - upper) * memoryBalance + upper;
        }
        else if (memoryName == this._promptOptions.WorkingMemoryName)
        {
            return (upper - lower) * memoryBalance + lower;
        }
        else
        {
            throw new ArgumentException($"Invalid memory name: {memoryName}");
        }
    }

    # endregion
}
