// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq.Expressions;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ProviderServices.Filter;

/// <summary>
/// A processor for user-provided filter expressions which performs various common transformations before actual translation takes place.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public class FilterTranslationPreprocessor : ExpressionVisitor
{
    private List<string>? _parameterNames;

    /// <summary>
    /// Whether the connector supports parameterization.
    /// </summary>
    /// <remarks>
    /// If <see langword="false"/>, the visitor will inline captured variables and constant member accesses as simple constant nodes.
    /// If <see langword="true"/>, these will instead be replaced with <see cref="QueryParameterExpression"/> nodes.
    /// </remarks>
    public required bool SupportsParameterization { get; init; }

    /// <summary>
    /// Preprocesses the filter expression before translation.
    /// </summary>
    public Expression Preprocess(Expression node)
    {
        if (this.SupportsParameterization)
        {
            this._parameterNames = [];
        }

        return this.Visit(node);
    }

    /// <inheritdoc />
    protected override Expression VisitMember(MemberExpression node)
    {
        var visited = (MemberExpression)base.VisitMember(node);

        // This identifies field and property access over constants, which can be evaluated immediately.
        // This covers captured variables, since those are actually member accesses over compiled-generated closure types:
        // var x = 8;
        // _ = await collection.SearchAsync(vector, top: 3, new() { Filter = r => r.Int == x });
        //
        // This also covers member variables:
        // _ = await collection.SearchAsync(vector, top: 3, new() { Filter = r => r.Int == this._x });
        // ... as "this" here is represented by a ConstantExpression node in the tree.
        //
        // Some databases - mostly relational ones - support out-of-band parameters which can be referenced via placeholders
        // from the query itself. For those databases, we transform the member access to QueryParameterExpression (this simplifies things for those
        // connectors, and centralizes the pattern matching in a single centralized place).
        // For databases which don't support parameters, we simply inline the evaluated member access as a constant in the tree, so that translators don't
        // even need to be aware of it.

        // Evaluate the MemberExpression to get the actual value, either for instance members (expression is a ConstantExpression) or for
        // static members (expression is null).
        object? baseValue;
        switch (visited.Expression)
        {
            // Member access over constant (i.e. instance members)
            case ConstantExpression { Value: var v }:
                baseValue = v;
                break;

            // Member constant over null (i.e. static members)
            case null:
                baseValue = null;
                break;

            // Member constant over something that has already been parameterized (i.e. nested member access, e.g. r=> r.Int == this.SomeWrapper.Something)
            case QueryParameterExpression p:
                baseValue = p.Value;

                // The previous parameter is getting replaced by the new one we're creating here, so remove its name from the list of parameter names.
                this._parameterNames!.Remove(p.Name);
                break;

            default:
                return visited;
        }

        object? evaluatedValue;

        var memberInfo = visited.Member;

        switch (memberInfo)
        {
            case FieldInfo fieldInfo:
                evaluatedValue = fieldInfo.GetValue(baseValue);
                break;

            case PropertyInfo { GetMethod.IsStatic: false } propertyInfo when baseValue is null:
                throw new InvalidOperationException($"Cannot access member '{propertyInfo.Name}' on null object.");

            case PropertyInfo propertyInfo:
                evaluatedValue = propertyInfo.GetValue(baseValue);
                break;
            default:
                return visited;
        }

        // Inline the evaluated value (if the connector doesn't support parameterization, or if the field is readonly),
        if (!this.SupportsParameterization)
        {
            return Expression.Constant(evaluatedValue, visited.Type);
        }

        // Otherwise, transform the node to a QueryParameterExpression which the connector will then translate to a parameter (e.g. SqlParameter).

        // TODO: Share the same parameter when it references the same captured value

        // Make sure parameter names are unique.
        var origName = memberInfo.Name;
        var name = origName;
        for (var i = 0; this._parameterNames!.Contains(name); i++)
        {
            name = $"{origName}_{i}";
        }
        this._parameterNames.Add(name);

        return new QueryParameterExpression(name, evaluatedValue, visited.Type);
    }
}
