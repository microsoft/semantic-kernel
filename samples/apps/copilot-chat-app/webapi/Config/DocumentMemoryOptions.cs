// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for handling memorized documents.
/// </summary>
public class DocumentMemoryOptions
{
    public const string PropertyName = "DocumentMemory";

    /// <summary>
    /// Gets or sets the name of the global document collection.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string GlobalDocumentCollectionName { get; set; } = "global-documents";

    /// <summary>
    /// Gets or sets the prefix for the user document collection name.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string UserDocumentCollectionNamePrefix { get; set; } = "user-documents-";

    /// <summary>
    /// Gets or sets the maximum number of tokens to use when splitting a document into lines.
    /// Default token limits are suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    /// </summary>
    [Range(0, int.MaxValue)]
    public int DocumentLineSplitMaxTokens { get; set; } = 30;

    /// <summary>
    /// Gets or sets the maximum number of lines to use when combining lines into paragraphs.
    /// Default token limits are suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    /// </summary>
    [Range(0, int.MaxValue)]
    public int DocumentParagraphSplitMaxLines { get; set; } = 100;

    /// <summary>
    /// Maximum size in bytes of a document to be allowed for importing.
    /// Prevent large uploads by setting a file size limit (in bytes) as suggested here:
    /// https://learn.microsoft.com/en-us/aspnet/core/mvc/models/file-uploads?view=aspnetcore-6.0
    /// </summary>
    [Range(0, int.MaxValue)]
    public int FileSizeLimit { get; set; } = 1000000;

    /// <summary>
    /// Similarity threshold to avoid document memory duplication when importing documents to memory.
    /// The higher the value, the more document memories can be similar without being eliminated as duplicates.
    /// </summary>
    [Range(0.0, 1.0)]
    public double DeduplicationSimilarityThreshold { get; set; } = 0.8;
}
