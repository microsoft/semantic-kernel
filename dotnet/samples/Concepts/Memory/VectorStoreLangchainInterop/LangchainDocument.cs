// Copyright (c) Microsoft. All rights reserved.

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Data model class that matches the data model used by Langchain.
/// This data model is not decorated with vector store attributes since instead
/// a different record definition is used with each vector store implementation.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public class LangchainDocument<TKey>
{
    /// <summary>
    /// The unique identifier of the record.
    /// </summary>
    public TKey Key { get; set; }

    /// <summary>
    /// The text content for which embeddings have been generated.
    /// </summary>
    public string Content { get; set; }

    /// <summary>
    /// The source of the content. E.g. where to find the original content.
    /// </summary>
    public string Source { get; set; }

    /// <summary>
    /// The embedding for the <see cref="Content"/>.
    /// </summary>
    public ReadOnlyMemory<float> Embedding { get; set; }
}
