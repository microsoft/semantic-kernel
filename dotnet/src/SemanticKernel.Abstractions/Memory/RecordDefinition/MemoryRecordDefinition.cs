// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A description of the properties of a record stored in a memory store, plus how the properties are used.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class MemoryRecordDefinition
{
    /// <summary>Empty static list for initialization purposes.</summary>
    private static readonly List<MemoryRecordProperty> s_emptyFields = new();

    /// <summary>
    /// The list of properties that are stored in the record.
    /// </summary>
    public IReadOnlyList<MemoryRecordProperty> Properties { get; init; } = s_emptyFields;
}
