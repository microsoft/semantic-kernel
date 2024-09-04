// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// FilterClause which filters by checking if a field consisting of a list of values contains a specific value.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class TagListContainsFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TagListContainsFilterClause"/> class.
    /// </summary>
    /// <param name="fieldName">The name of the field with the list of values.</param>
    /// <param name="value">The value that the list should contain.</param>
    internal TagListContainsFilterClause(string fieldName, string value) : base(FilterClauseType.TagListContains)
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
