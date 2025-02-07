// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Describes the properties of a record stored in a vector store.
/// </summary>
/// <remarks>
/// Each property contains additional information about how the property will be treated by the vector store.
/// </remarks>
public sealed class VectorStoreRecordDefinition
{
    /// <summary>Empty static list for initialization purposes.</summary>
    private static readonly List<VectorStoreRecordProperty> s_emptyFields = new();

    /// <summary>
    /// Gets or sets the list of properties that are stored in the record.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordProperty> Properties { get; init; } = s_emptyFields;
}
