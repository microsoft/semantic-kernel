// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Optional options when calling <see cref="IVectorRecordStore{TKey, TDataModel}.DeleteAsync"/>.
/// Reserved for future use.
/// </summary>
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
