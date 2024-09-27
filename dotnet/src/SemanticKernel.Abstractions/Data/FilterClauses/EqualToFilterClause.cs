// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// <see cref="FilterClause"/> which filters using equality of a field value.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class EqualToFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="EqualToFilterClause"/> class.
    /// </summary>
    /// <param name="fieldName">Field name.</param>
    /// <param name="value">Field value.</param>
    internal EqualToFilterClause(string fieldName, object value)
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
