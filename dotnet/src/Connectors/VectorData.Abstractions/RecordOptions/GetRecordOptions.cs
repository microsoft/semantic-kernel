// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.GetAsync(TKey, Microsoft.Extensions.VectorData.GetRecordOptions?, System.Threading.CancellationToken)"/>.
/// </summary>
public class GetRecordOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GetRecordOptions"/> class.
    /// </summary>
    public GetRecordOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GetRecordOptions"/> class by cloning the given options.
    /// </summary>
    /// <param name="source">The options to clone.</param>
    public GetRecordOptions(GetRecordOptions source)
    {
        this.IncludeVectors = source.IncludeVectors;
    }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
