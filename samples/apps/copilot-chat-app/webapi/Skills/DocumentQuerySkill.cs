// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions.Partitioning;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.Service.Skills;

/// <summary>
///
/// </summary>
public class DocumentQuerySkill
{
    /// <summary>
    /// Returns the name of the semantic document memory collection that stores document semantic memory.
    /// </summary>
    /// <param name="userId">ID of the user who owns the documents.</param>
    internal static string DocumentMemoryCollectionName(string userId) => $"{userId}-documents";

    /// <summary>
    /// Prompt settings.
    /// </summary>
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// Create a new instance of DocumentQuerySkill.
    /// </summary>
    public DocumentQuerySkill(PromptSettings promptSettings)
    {
        this._promptSettings = promptSettings;
    }

    /// <summary>
    /// Parse a local file into embeddings.
    /// </summary>
    /// <param name="localFile">Path to the local file including the file name.</param>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Parse a local file")]
    [SKFunctionName("ParseLocalFile")]
    [SKFunctionInput(Description = "Path to the local file including the file name.")]
    [SKFunctionContextParameter(Name = "userId", Description = "ID of the user who owns the documents.")]
    public async Task ParseLocalFileAsync(string localFile, SKContext context)
    {
        string userId = context.Variables["userId"];

        string text = string.Empty;
        try
        {
            text = File.ReadAllText(localFile);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to read local file: {0}", ex.Message);
            context.Fail($"Unable to read local file: {ex.Message}", ex);
            return;
        }

        var lines =
            SemanticTextPartitioner.SplitPlainTextLines(text, this._promptSettings.DocumentLineSplitMaxTokens);
        var paragraphs =
            SemanticTextPartitioner.SplitPlainTextParagraphs(lines, this._promptSettings.DocumentParagraphSplitMaxLines);
        foreach (var paragraph in paragraphs)
        {
            await context.Memory.SaveInformationAsync(
                collection: DocumentMemoryCollectionName(userId),
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
        int tokenLimit = int.Parse(context.Variables["tokenLimit"]);
        int contextTokenLimit = int.Parse(context.Variables["contextTokenLimit"]);
        var remainingToken = Math.Min(
            tokenLimit,
            Math.Floor(contextTokenLimit * this._promptSettings.DocumentContextWeight)
        );

        var results = context.Memory.SearchAsync
        (
            collection: DocumentMemoryCollectionName(userId),
            query: query,
            limit: 1000,
            minRelevanceScore: 0.8,
            withEmbeddings: false,
            cancel: context.CancellationToken
        );

        string documentsText = string.Empty;
        await foreach (var memory in results)
        {
            var estimatedTokenCount = Utils.EstimateTokenCount(
                memory.Metadata.Text,
                this._promptSettings.TokenEstimateFactor
            );

            if (remainingToken - estimatedTokenCount > 0)
            {
                documentsText += $"\n\nSnippet from {memory.Metadata.Description}: {memory.Metadata.Text}";
                remainingToken -= estimatedTokenCount;
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
        tokenLimit -= Utils.EstimateTokenCount(documentsText, this._promptSettings.TokenEstimateFactor);
        context.Variables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        return documentsText;
    }
}