// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions.Partitioning;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// This skill provides the ability to parse a file into embeddings and query the document memory.
/// </summary>
public class DocumentMemorySkill
{
    /// <summary>
    /// Returns the name of the semantic document memory collection that stores document semantic memory.
    /// </summary>
    /// <param name="userId">ID of the user who owns the documents.</param>
    internal string UserDocumentMemoryCollectionName(string userId) => $"{userId}-documents";

    /// <summary>
    /// Name of the semantic document memory collection that stores document semantic memory globally
    /// available to users accessing the service.
    /// </summary>
    internal string GlobalDocumentMemoryCollectionName = "global-documents";

    /// <summary>
    /// Prompt settings.
    /// </summary>
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// Create a new instance of DocumentMemorySkill.
    /// </summary>
    public DocumentMemorySkill(PromptSettings promptSettings)
    {
        this._promptSettings = promptSettings;
    }

    /// <summary>
    /// Parse a local file into embeddings.
    /// </summary>
    /// <param name="localFile">Path to the local file including the file name.</param>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Parse a local file on disk into embeddings and save the embeddings to the document memory for querying.")]
    [SKFunctionName("ParseLocalFile")]
    [SKFunctionInput(Description = "Path to the local file including the file name.")]
    [SKFunctionContextParameter(
        Name = "userId",
        Description = "ID of the user who owns the documents. This is used to create a unique collection name for the user." +
                      "If the user ID is not specified or empty, the documents will be stored in a global collection.",
        DefaultValue = "")]
    public async Task ParseLocalFileAsync(string localFile, SKContext context)
    {
        string collection = context.Variables.ContainsKey("userID") ?
            string.IsNullOrEmpty(context.Variables["userID"]) ?
                this.GlobalDocumentMemoryCollectionName :
                this.UserDocumentMemoryCollectionName(context.Variables["userID"]) :
            this.GlobalDocumentMemoryCollectionName;

        string text = string.Empty;
        try
        {
            text = await File.ReadAllTextAsync(localFile, context.CancellationToken);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to read local file: {0}", ex.Message);
            context.Fail($"Unable to read local file: {ex.Message}", ex);
            return;
        }

        var lines = SemanticTextPartitioner.SplitPlainTextLines(
            text, this._promptSettings.DocumentLineSplitMaxTokens);
        var paragraphs = SemanticTextPartitioner.SplitPlainTextParagraphs(
            lines, this._promptSettings.DocumentParagraphSplitMaxLines);
        foreach (var paragraph in paragraphs)
        {
            await context.Memory.SaveInformationAsync(
                collection: collection,
                text: paragraph,
                id: Guid.NewGuid().ToString(),
                description: $"Document: {localFile}");
        }

        context.Log.LogInformation("Parsed {0} paragraphs from local file {1}", paragraphs.Count, localFile);
    }

    /// <summary>
    /// Query the document memory collection for documents that match the query.
    /// </summary>
    /// <param name="query">Query to match.</param>
    /// <param name="context">Contains the memory.</param>
    [SKFunction("Query documents in the memory given a user message")]
    [SKFunctionName("QueryDocuments")]
    [SKFunctionInput(Description = "Query to match.")]
    [SKFunctionContextParameter(Name = "userId", Description = "ID of the user who owns the documents")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    [SKFunctionContextParameter(Name = "contextTokenLimit", Description = "Maximum number of context tokens")]
    public async Task<string> QueryDocumentsAsync(string query, SKContext context)
    {
        string userId = context.Variables["userId"];
        int tokenLimit = int.Parse(context.Variables["tokenLimit"], new NumberFormatInfo());
        int contextTokenLimit = int.Parse(context.Variables["contextTokenLimit"], new NumberFormatInfo());
        var remainingToken = Math.Min(
            tokenLimit,
            Math.Floor(contextTokenLimit * this._promptSettings.DocumentContextWeight)
        );

        // Search for relevant document snippets.
        string[] documentCollections = new string[]
        {
            this.UserDocumentMemoryCollectionName(userId),
            this.GlobalDocumentMemoryCollectionName
        };

        List<MemoryQueryResult> relevantMemories = new List<MemoryQueryResult>();
        foreach (var documentCollection in documentCollections)
        {
            var results = context.Memory.SearchAsync(
                documentCollection,
                query,
                limit: 100,
                minRelevanceScore: 0.8);
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
            var tokenCount = Utils.TokenCount(memory.Metadata.Text);
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
        tokenLimit -= Utils.TokenCount(documentsText);
        context.Variables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        return documentsText;
    }
}
