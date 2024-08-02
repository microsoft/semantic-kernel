// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options when calling <see cref="IVectorStoreRecordCollection{TKey, TDataModel}.DeleteAsync"/>.
/// </summary>
/// <remarks>
/// This class does not currently include any options, but is added for future extensibility of the API.
/// </remarks>
[Experimental("SKEXP0001")]
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
    /// <param name="source">The options to clone</param>
    public DeleteRecordOptions(DeleteRecordOptions source)
    {
    }
}
