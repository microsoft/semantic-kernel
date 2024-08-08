// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// FilterClause which filters using equality of a field value.
/// </summary>
/// <remarks>
/// Constructs an instance of <see cref="EqualityFilterClause"/>
/// </remarks>
/// <param name="field">Field name.</param>
/// <param name="value">Field value.</param>
public sealed class EqualityFilterClause(string field, object value) : FilterClause(FilterClauseType.Equality)
{
    /// <summary>
    /// Filed name to match.
    /// </summary>
    public string Field { get; private set; } = field;

    /// <summary>
    /// Field value to match.
    /// </summary>
    public object Value { get; private set; } = value;
}
