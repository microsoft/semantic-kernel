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
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; set; }
}
