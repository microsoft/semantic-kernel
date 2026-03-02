// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for hybrid search when using a dense vector and string keywords to do the search.
/// </summary>
public class HybridSearchOptions<TRecord>
{
    private int _skip = 0;

    /// <summary>
    /// Gets or sets a search filter to use before doing the hybrid search.
    /// </summary>
#pragma warning disable CS0618 // Type or member is obsolete
    [Obsolete("Use Filter instead")]
    public VectorSearchFilter? OldFilter { get; set; }
#pragma warning restore CS0618 // Type or member is obsolete

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    public Expression<Func<TRecord, bool>>? Filter { get; set; }

    /// <summary>
    /// Gets or sets the target dense vector property to search on.
    /// Only needs to be set when the collection has multiple vector properties.
    /// </summary>
    /// <remarks>
    /// If this property isn't set, <see cref="IKeywordHybridSearchable{TRecord}.HybridSearchAsync{TInput}(TInput, System.Collections.Generic.ICollection{string}, int, Microsoft.Extensions.VectorData.HybridSearchOptions{TRecord}?, System.Threading.CancellationToken)"/> checks if there is a vector property to use by default, and
    /// throws if either none or multiple exist.
    /// </remarks>
    public Expression<Func<TRecord, object?>>? VectorProperty { get; set; }

    /// <summary>
    /// Gets or sets the additional target property to do the text or keyword search on.
    /// The property must have full text indexing enabled.
    /// </summary>
    /// <remarks>
    /// If this property isn't set, <see cref="IKeywordHybridSearchable{TRecord}.HybridSearchAsync{TInput}(TInput, System.Collections.Generic.ICollection{string}, int, Microsoft.Extensions.VectorData.HybridSearchOptions{TRecord}?, System.Threading.CancellationToken)"/> checks if there is a text property with full text indexing enabled, and
    /// throws an exception if either none or multiple exist.
    /// </remarks>
    public Expression<Func<TRecord, object?>>? AdditionalProperty { get; set; }

    /// <summary>
    /// Gets or sets the number of results to skip before returning results, that is, the index of the first result to return.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">The value is less than 0.</exception>
    public int Skip
    {
        get => this._skip;
        set
        {
            if (value < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Skip must be greater than or equal to 0.");
            }

            this._skip = value;
        }
    }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; set; }

    /// <summary>
    /// Gets or sets the score threshold to filter results.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The meaning of the score is a combination of the distance function configured for <see cref="VectorProperty"/> and the text
    /// relevance score for the full-text search on <see cref="AdditionalProperty"/>.
    /// </para>
    /// <para>
    /// The range of scores also depends on the distance function; for example, cosine similarity/distance scores
    /// fall within 0 to 1, while Euclidean distance is unbounded. Scores can also differ between vector databases.
    /// </para>
    /// </remarks>
    public double? ScoreThreshold { get; set; }
}
