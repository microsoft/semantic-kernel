// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options to use with the <see cref="IVectorStoreRecordMapper{TRecordDataModel, TStorageModel}.MapFromStorageToDataModel"/> method.
/// </summary>
[Experimental("SKEXP0001")]
public class StorageToDataModelMapperOptions
{
    /// <summary>
    /// Get or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
