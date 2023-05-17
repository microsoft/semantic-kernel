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
using SemanticKernel.Service.CopilotChat.Storage;

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
    /// A repository to save and retrieve chat messages.
    /// </summary>
    private readonly ChatMessageRepository _chatMessageRepository;

    /// <summary>
    /// Create a new instance of SemanticChatMemorySkill.
    /// </summary>
    public SemanticChatMemorySkill(
        IOptions<PromptsOptions> promptOptions,
        ChatMessageRepository chatMessageRepository)
    {
        this._promptOptions = promptOptions.Value;
        this._chatMessageRepository = chatMessageRepository;
    }

    /// <summary>
    /// Query relevant memories based on the latest message.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <returns>A string containing the relevant memories.</returns>
    [SKFunction("Query user memories")]
    [SKFunctionName("QueryUserMemories")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to query history from")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> QueryUserMemoriesAsync(SKContext context)
    {
        var chatId = context["chatId"];
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var remainingToken = tokenLimit;

        // Find the most recent message.
        var latestMessage = await this._chatMessageRepository.FindLastByChatIdAsync(chatId);

        // Search for relevant memories.
        List<MemoryQueryResult> relevantMemories = new();
        foreach (var memoryName in this._promptOptions.MemoryMap.Keys)
        {
            var results = context.Memory.SearchAsync(
                SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName),
                latestMessage.ToString(),
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

        return $"Past memories (format: [memory type] <label>: <details>):\n{memoryText.Trim()}";
    }
}
