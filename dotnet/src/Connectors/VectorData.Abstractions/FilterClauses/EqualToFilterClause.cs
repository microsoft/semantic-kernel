// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// <see cref="FilterClause"/> which filters using equality of a field value.
/// </summary>
public sealed class EqualToFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="EqualToFilterClause"/> class.
    /// </summary>
    /// <param name="fieldName">Field name.</param>
    /// <param name="value">Field value.</param>
    public EqualToFilterClause(string fieldName, object value)
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
