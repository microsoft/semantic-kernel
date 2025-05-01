// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Microsoft.Extensions.VectorData.ConnectorSupport.Filter;

/// <summary>
/// A processor for user-provided filter expressions which performs various common transformations before actual translation takes place.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class FilterTranslationPreprocessor : ExpressionVisitor
{
    /// <summary>
    /// Whether to inline captured variables in the filter expression (when the database doesn't support parameters).
    /// </summary>
    public bool InlineCapturedVariables { get; init; }

    /// <summary>
    /// Whether to transform captured variables in the filter expression to <see cref="QueryParameterExpression"/> (when the database supports parameters).
    /// </summary>
    public bool TransformCapturedVariablesToQueryParameterExpressions { get; init; }

    /// <inheritdoc />
    protected override Expression VisitMember(MemberExpression node)
    {
        // This identifies compiler-generated closure types which contain captured variables.
        // Some databases - mostly relational ones - support out-of-band parameters which can be referenced via placeholders
        // from the query itself. For those databases, we transform the captured variable to QueryParameterExpression (this simplifies things for those
        // connectors, and centralizes the pattern matching in a single centralized place).
        // For databases which don't support parameters, we simply inline the captured variable as a constant in the tree, so that translators don't
        // even need to be aware of the captured variable.
        // For all other databases, we simply inline the captured variable as a constant in the tree.
        if (node is MemberExpression { Expression: ConstantExpression constant, Member: FieldInfo fieldInfo }
            && constant.Type.Attributes.HasFlag(TypeAttributes.NestedPrivate)
            && Attribute.IsDefined(constant.Type, typeof(CompilerGeneratedAttribute), inherit: true))
        {
            return (this.InlineCapturedVariables, this.TransformCapturedVariablesToQueryParameterExpressions) switch
            {
                (true, false) => Expression.Constant(fieldInfo.GetValue(constant.Value), node.Type),
                (false, true) => new QueryParameterExpression(fieldInfo.Name, fieldInfo.GetValue(constant.Value), node.Type),

                (true, true) => throw new InvalidOperationException("InlineCapturedVariables and TransformCapturedVariablesToQueryParameterExpressions cannot both be true."),
                (false, false) => base.VisitMember(node)
            };
        }

        return base.VisitMember(node);
    }
}
