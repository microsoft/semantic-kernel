// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.DeleteAsync"/>.
/// </summary>
/// <remarks>
/// This class does not currently include any options, but is added for future extensibility of the API.
/// </remarks>
public class DeleteRecordOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="DeleteRecordOptions"/> class.
    /// </summary>
    public DeleteRecordOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DeleteRecordOptions"/> class by cloning the given options.
    /// </summary>
    /// <param name="source">The options to clone.</param>
    public DeleteRecordOptions(DeleteRecordOptions source)
    {
    }
}
