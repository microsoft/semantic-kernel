// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// FilterClause which filters using equality of a field value.
/// </summary>
/// <remarks>
/// Constructs an instance of <see cref="EqualityFilterClause"/>
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class EqualityFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="EqualityFilterClause"/> class.
    /// </summary>
    /// <param name="fieldName">Field name.</param>
    /// <param name="value">Field value.</param>
    internal EqualityFilterClause(string fieldName, object value) : base(FilterClauseType.Equality)
    {
        this.FieldName = fieldName;
        this.Value = value;
    }

    /// <summary>
    /// Field name to match.
    /// </summary>
    public string FieldName { get; private set; }

    /// <summary>
    /// Field value to match.
    /// </summary>
    public object Value { get; private set; }
}
