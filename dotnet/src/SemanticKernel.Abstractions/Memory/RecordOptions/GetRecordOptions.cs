// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Optional options when calling <see cref="IMemoryRecordService{TKey, TDataModel}.GetAsync"/>.
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
        this.CollectionName = source.CollectionName;
        this.IncludeVectors = source.IncludeVectors;
    }

    /// <summary>
    /// Get or sets an optional collection name to use for this operation that is different to the default.
    /// </summary>
    public string? CollectionName { get; init; }

    /// <summary>
    /// Get or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
