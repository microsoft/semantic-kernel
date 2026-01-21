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

    /// <inheritdoc />
    protected override Expression VisitNew(NewExpression node)
    {
        var visited = (NewExpression)base.VisitNew(node);

        // Recognize certain well-known constructors where we can evaluate immediately, converting the NewExpression to a ConstantExpression.
        // This is particularly useful for converting inline instantiation of DateTime and DateTimeOffset to constants, which can then be easily translated.
        switch (visited.Constructor)
        {
            case ConstructorInfo constructor when constructor.DeclaringType == typeof(DateTimeOffset) || constructor.DeclaringType == typeof(DateTime):
                var constantArguments = new object?[visited.Arguments.Count];

                // We first do a fast path to check if all arguments are constants; this catches the common case of e.g. new DateTime(2023, 10, 1).
                // If an argument isn't a constant (e.g. new DateTimeOffset(..., TimeSpan.FromHours(2))), we fall back to trying the LINQ interpreter
                // as a general-purpose expression evaluator - but note that this is considerably slower.
                for (var i = 0; i < visited.Arguments.Count; i++)
                {
                    if (visited.Arguments[i] is ConstantExpression constantArgument)
                    {
                        constantArguments[i] = constantArgument.Value;
                    }
                    else
                    {
                        // There's a non-constant argument - try the LINQ interpreter.
#pragma warning disable CA1031 // Do not catch general exception types
                        try
                        {
                            var evaluated = Expression.Lambda<Func<object>>(Expression.Convert(visited, typeof(object)))
#if NET
                                .Compile(preferInterpretation: true)
#else
                                .Compile()
#endif
                                .Invoke();

                            return Expression.Constant(evaluated, constructor.DeclaringType);
                        }
                        catch
                        {
                            return visited;
                        }
#pragma warning restore CA1031
                    }
                }

                var constantValue = constructor.Invoke(constantArguments);
                return Expression.Constant(constantValue, constructor.DeclaringType);
        }

        return visited;
    }
}
