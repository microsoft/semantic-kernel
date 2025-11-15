// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Reranking;

/// <summary>
/// Represents a single reranking result containing a document and its relevance score.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class RerankResult
{
    /// <summary>
    /// Gets the index of the document in the original input list.
    /// </summary>
    public int Index { get; }

    /// <summary>
    /// Gets the document text.
    /// </summary>
    public string Text { get; }

    /// <summary>
    /// Gets the relevance score assigned by the reranker.
    /// Higher scores indicate greater relevance to the query.
    /// </summary>
    public double RelevanceScore { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RerankResult"/> class.
    /// </summary>
    /// <param name="index">The index of the document in the original input list.</param>
    /// <param name="text">The document text.</param>
    /// <param name="relevanceScore">The relevance score.</param>
    public RerankResult(int index, string text, double relevanceScore)
    {
        this.Index = index;
        this.Text = text ?? throw new ArgumentNullException(nameof(text));
        this.RelevanceScore = relevanceScore;
    }
}
