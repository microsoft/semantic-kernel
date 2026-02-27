// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for vector search via <see cref="VectorStoreCollection{TKey, TRecord}.SearchAsync{TInput}(TInput, int, VectorSearchOptions{TRecord}, CancellationToken)"/>.
/// </summary>
public class VectorSearchOptions<TRecord>
{
    private int _skip = 0;

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    [Obsolete("Use Filter instead")]
    public VectorSearchFilter? OldFilter { get; set; }

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    public Expression<Func<TRecord, bool>>? Filter { get; set; }

    /// <summary>
    /// Gets or sets the vector property to search on.
    /// Only needs to be set when the collection has multiple vector properties.
    /// </summary>
    /// <remarks>
    /// If this property isn't set provided, <see cref="VectorStoreCollection{TKey, TRecord}.SearchAsync{TInput}(TInput, int, VectorSearchOptions{TRecord}, CancellationToken)"/> checks if there is a vector property to use by default, and
    /// throws an exception if either none or multiple exist.
    /// </remarks>
    public Expression<Func<TRecord, object?>>? VectorProperty { get; set; }

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
    /// The meaning of the score depends on the distance function configured for the vector property.
    /// For similarity functions (e.g. <see cref="DistanceFunction.CosineSimilarity" />, <see cref="DistanceFunction.DotProductSimilarity" />),
    /// higher scores indicate more similar results, and results with scores lower than the threshold will be filtered out.
    /// For distance functions (e.g. <see cref="DistanceFunction.CosineDistance" />, <see cref="DistanceFunction.EuclideanDistance" />),
    /// lower scores indicate more similar results, and results with scores higher than the threshold will be filtered out.
    /// </para>
    /// <para>
    /// The range of scores also depends on the distance function; for example, cosine similarity/distance scores
    /// fall within 0 to 1, while Euclidean distance is unbounded. Scores can also differ between vector databases.
    /// </para>
    /// </remarks>
    public double? ScoreThreshold { get; set; }
}
