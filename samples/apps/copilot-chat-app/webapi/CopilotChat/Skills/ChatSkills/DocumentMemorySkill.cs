// Copyright (c) Microsoft. All rights reserved.

using System;
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
/// This skill provides the functions to query the document memory.
/// </summary>
public class DocumentMemorySkill
{
    /// <summary>
    /// Prompt settings.
    /// </summary>
    private readonly PromptsOptions _promptOptions;

    /// <summary>
    /// Configuration settings for importing documents to memory.
    /// </summary>
    private readonly DocumentMemoryOptions _documentImportConfig;

    /// <summary>
    /// Create a new instance of DocumentMemorySkill.
    /// </summary>
    public DocumentMemorySkill(IOptions<PromptsOptions> promptOptions, DocumentMemoryOptions documentImportConfig)
    {
        this._promptOptions = promptOptions.Value;
        this._documentImportConfig = documentImportConfig;
    }

    /// <summary>
    /// Query the document memory collection for documents that match the query.
    /// </summary>
    /// <param name="query">Query to match.</param>
    /// <param name="context">Contains the memory.</param>
    [SKFunction("Query documents in the memory given a user message")]
    [SKFunctionName("QueryDocuments")]
    [SKFunctionInput(Description = "Query to match.")]
    [SKFunctionContextParameter(Name = "chatId", Description = "ID of the chat that owns the documents")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    [SKFunctionContextParameter(Name = "contextTokenLimit", Description = "Maximum number of context tokens")]
    public async Task<string> QueryDocumentsAsync(string query, SKContext context)
    {
        string chatId = context.Variables["chatId"];
        int tokenLimit = int.Parse(context.Variables["tokenLimit"], new NumberFormatInfo());
        int contextTokenLimit = int.Parse(context.Variables["contextTokenLimit"], new NumberFormatInfo());
        var remainingToken = Math.Min(
            tokenLimit,
            Math.Floor(contextTokenLimit * this._promptOptions.DocumentContextWeight)
        );

        // Search for relevant document snippets.
        string[] documentCollections = new string[]
        {
            this._documentImportConfig.ChatDocumentCollectionNamePrefix + chatId,
            this._documentImportConfig.GlobalDocumentCollectionName
        };

        List<MemoryQueryResult> relevantMemories = new();
        foreach (var documentCollection in documentCollections)
        {
            var results = context.Memory.SearchAsync(
                documentCollection,
                query,
                limit: 100,
                minRelevanceScore: this._promptOptions.DocumentMemoryMinRelevance);
            await foreach (var memory in results)
            {
                relevantMemories.Add(memory);
            }
        }

        relevantMemories = relevantMemories.OrderByDescending(m => m.Relevance).ToList();

        // Concatenate the relevant document snippets.
        string documentsText = string.Empty;
        foreach (var memory in relevantMemories)
        {
            var tokenCount = Utilities.TokenCount(memory.Metadata.Text);
            if (remainingToken - tokenCount > 0)
            {
                documentsText += $"\n\nSnippet from {memory.Metadata.Description}: {memory.Metadata.Text}";
                remainingToken -= tokenCount;
            }
            else
            {
                break;
            }
        }

        if (string.IsNullOrEmpty(documentsText))
        {
            // No relevant documents found
            return string.Empty;
        }

        // Update the token limit.
        documentsText = $"User has also shared some document snippets:\n{documentsText}";
        tokenLimit -= Utilities.TokenCount(documentsText);
        context.Variables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        return documentsText;
    }
}
