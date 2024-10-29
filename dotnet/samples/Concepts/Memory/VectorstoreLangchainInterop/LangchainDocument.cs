// Copyright (c) Microsoft. All rights reserved.

namespace Memory.VectorstoreLangchainInterop;

/// <summary>
/// Data model class to use for Langchain interoperability samples
/// </summary>
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
