// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData.ConnectorSupport.Filter;

/// <summary>
/// An expression representation a query parameter (captured variable) in the filter expression.
/// </summary>
[Experimental("MEVD9001")]
public class QueryParameterExpression(string name, object? value, Type type) : Expression
{
    /// <summary>
    /// The name of the parameter.
    /// </summary>
    public string Name { get; } = name;

    /// <summary>
    /// The value of the parameter.
    /// </summary>
    public object? Value { get; } = value;

    /// <inheritdoc />
    public override ExpressionType NodeType => ExpressionType.Extension;

    /// <inheritdoc />
    public override Type Type => type;

    /// <inheritdoc />
    protected override Expression VisitChildren(ExpressionVisitor visitor) => this;
}
