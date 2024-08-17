// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A description of the properties of a record stored in a vector store.
/// </summary>
/// <remarks>
/// Each property contains additional information about how the property will be treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordDefinition
{
    /// <summary>Empty static list for initialization purposes.</summary>
    private static readonly List<VectorStoreRecordProperty> s_emptyFields = new();

    /// <summary>
    /// The list of properties that are stored in the record.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordProperty> Properties { get; init; } = s_emptyFields;
}
