// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// This skill provides the functions to query the document memory.
/// </summary>
public class DocumentMemorySkill
{
    /// <summary>
    /// Prompt settings.
    /// </summary>
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// Configuration settings for importing documents to memory.
    /// </summary>
    private readonly DocumentMemoryOptions _documentImportConfig;

    /// <summary>
    /// Create a new instance of DocumentMemorySkill.
    /// </summary>
    public DocumentMemorySkill(PromptSettings promptSettings, DocumentMemoryOptions documentImportConfig)
    {
        this._promptSettings = promptSettings;
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
            Math.Floor(contextTokenLimit * this._promptSettings.DocumentContextWeight)
        );

        // Search for relevant document snippets.
        string[] documentCollections = new string[]
        {
            this._documentImportConfig.ChatDocumentCollectionNamePrefix + chatId,
            this._documentImportConfig.GlobalDocumentCollectionName
        };

        List<MemoryQueryResult> relevantMemories = new List<MemoryQueryResult>();
        foreach (var documentCollection in documentCollections)
        {
            var results = context.Memory.SearchAsync(
                documentCollection,
                query,
                limit: 100,
                minRelevanceScore: this._promptSettings.DocumentMemoryMinRelevance);
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
