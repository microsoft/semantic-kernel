// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for calling <see cref="VectorStoreCollection{TKey, TRecord}.GetAsync(TKey, RecordRetrievalOptions?, CancellationToken)"/>
/// or <see cref="VectorStoreCollection{TKey, TRecord}.GetAsync(IEnumerable{TKey}, RecordRetrievalOptions?, CancellationToken)"/>.
/// </summary>
public class RecordRetrievalOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="RecordRetrievalOptions"/> class.
    /// </summary>
    public RecordRetrievalOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RecordRetrievalOptions"/> class by cloning the given options.
    /// </summary>
    /// <param name="source">The options to clone.</param>
    public RecordRetrievalOptions(RecordRetrievalOptions source)
    {
        this.IncludeVectors = source.IncludeVectors;
    }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
