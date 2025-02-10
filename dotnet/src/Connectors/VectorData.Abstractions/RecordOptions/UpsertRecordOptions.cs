// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.UpsertAsync"/>.
/// Reserved for future use.
/// </summary>
/// <remarks>
/// This class does not currently include any options, but is added for future extensibility of the API.
/// </remarks>
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
    /// <param name="source">The options to clone.</param>
    public UpsertRecordOptions(UpsertRecordOptions source)
    {
    }
}
