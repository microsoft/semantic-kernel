// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// A <see cref="FilterClause"/> which filters using equality of a field value with the specified field value.
/// </summary>
/// <remarks>
/// The <see cref="EqualityFilterClause"/> is used to request that the underlying search service should
/// filter search results based on the equality of a field value with the specified field value.
/// </remarks>
/// <param name="fieldName">Field name.</param>
/// <param name="value">Field value.</param>
[Experimental("SKEXP0001")]
public sealed class EqualityFilterClause(string fieldName, object value) : FilterClause
{
    /// <summary>
    /// Field name to match.
    /// </summary>
    public string FieldName { get; private set; } = fieldName;

    /// <summary>
    /// Field value to match.
    /// </summary>
    public object Value { get; private set; } = value;
}
