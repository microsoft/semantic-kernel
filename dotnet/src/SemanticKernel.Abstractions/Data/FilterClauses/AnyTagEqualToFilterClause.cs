// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// <see cref="FilterClause"/> which filters by checking if a field consisting of a list of values contains a specific value.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class AnyTagEqualToFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AnyTagEqualToFilterClause"/> class.
    /// </summary>
    /// <param name="fieldName">The name of the field with the list of values.</param>
    /// <param name="value">The value that the list should contain.</param>
    internal AnyTagEqualToFilterClause(string fieldName, string value)
    {
        this.FieldName = fieldName;
        this.Value = value;
    }

    /// <summary>
    /// The name of the field with the list of values.
    /// </summary>
    public string FieldName { get; private set; }

    /// <summary>
    /// The value that the list should contain.
    /// </summary>
    public string Value { get; private set; }
}
