// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration settings for importing documents to memory.
/// </summary>
public class DocumentImportConfig
{
    /// <summary>
    /// Gets or sets the name of the global document collection.
    /// </summary>
    public string GlobalDocumentCollectionName { get; set; } = "global-documents";

    /// <summary>
    /// Gets or sets the prefix for the user document collection name.
    /// </summary>
    public string UserDocumentCollectionNamePrefix { get; set; } = "user-documents-";

    /// <summary>
    /// Gets or sets the maximum number of tokens to use when splitting a document into lines.
    /// </summary>
    public int DocumentLineSplitMaxTokens { get; set; } = 30;

    /// <summary>
    /// Gets or sets the maximum number of lines to use when combining lines into paragraphs.
    /// </summary>
    public int DocumentParagraphSplitMaxLines { get; set; } = 100;
}
