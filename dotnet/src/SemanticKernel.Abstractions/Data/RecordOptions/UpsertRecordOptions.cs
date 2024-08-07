// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options when calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.UpsertAsync"/>.
/// Reserved for future use.
/// </summary>
/// <remarks>
/// This class does not currently include any options, but is added for future extensibility of the API.
/// </remarks>
[Experimental("SKEXP0001")]
public class UpsertRecordOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertRecordOptions"/> class.
    /// </summary>
    public UpsertRecordOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertRecordOptions"/> class by cloning the given options.
    /// </summary>
    /// <param name="source">The options to clone</param>
    public UpsertRecordOptions(UpsertRecordOptions source)
    {
    }
}
