// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options when calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.GetAsync"/>.
/// </summary>
[Experimental("SKEXP0001")]
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
    /// <param name="source">The options to clone</param>
    public GetRecordOptions(GetRecordOptions source)
    {
        this.IncludeVectors = source.IncludeVectors;
    }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
