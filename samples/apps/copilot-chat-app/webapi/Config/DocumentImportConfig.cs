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
    /// Default token limits are suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    /// </summary>
    public int DocumentLineSplitMaxTokens { get; set; } = 30;

    /// <summary>
    /// Gets or sets the maximum number of lines to use when combining lines into paragraphs.
    /// Default token limits are suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    /// </summary>
    public int DocumentParagraphSplitMaxLines { get; set; } = 100;

    /// <summary>
    /// Maximum size in bytes of a document to be allowed for importing.
    /// Prevent large uploads by setting a file size limit (in bytes) as suggested here:
    /// https://learn.microsoft.com/en-us/aspnet/core/mvc/models/file-uploads?view=aspnetcore-6.0
    /// </summary>
    public int FileSizeLimit { get; set; } = 1000000;
}
