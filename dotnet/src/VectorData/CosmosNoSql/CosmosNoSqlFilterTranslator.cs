// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

#pragma warning disable MEVD9001 // Experimental: filter translation base types

internal class CosmosNoSqlFilterTranslator : FilterTranslatorBase
{
    private readonly Dictionary<string, object?> _parameters = [];
    private readonly StringBuilder _sql = new();

    internal (string WhereClause, Dictionary<string, object?> Parameters) Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        var preprocessedExpression = this.PreprocessFilter(lambdaExpression, model, new FilterPreprocessingOptions { SupportsParameterization = true });

        this.Translate(preprocessedExpression);

        return (this._sql.ToString(), this._parameters);
    }

    private void Translate(Expression? node)
    {
        switch (node)
        {
            case BinaryExpression binary:
                this.TranslateBinary(binary);
                return;

            case ConstantExpression constant:
                this.TranslateConstant(constant);
                return;

            case QueryParameterExpression { Name: var name, Value: var value }:
                this.TranslateQueryParameter(name, value);
                return;

            case MemberExpression member:
                this.TranslateMember(member);
                return;

            case NewArrayExpression newArray:
                this.TranslateNewArray(newArray);
                return;

            case MethodCallExpression methodCall:
                this.TranslateMethodCall(methodCall);
                return;

            case UnaryExpression unary:
                this.TranslateUnary(unary);
                return;

            default:
                throw new NotSupportedException("Unsupported NodeType in filter: " + node?.NodeType);
        }
    }

    private void TranslateBinary(BinaryExpression binary)
    {
        this._sql.Append('(');
        this.Translate(binary.Left);

        this._sql.Append(binary.NodeType switch
        {
            ExpressionType.Equal => " = ",
            ExpressionType.NotEqual => " <> ",

            ExpressionType.GreaterThan => " > ",
            ExpressionType.GreaterThanOrEqual => " >= ",
            ExpressionType.LessThan => " < ",
            ExpressionType.LessThanOrEqual => " <= ",

            ExpressionType.AndAlso => " AND ",
            ExpressionType.OrElse => " OR ",

            _ => throw new NotSupportedException("Unsupported binary expression node type: " + binary.NodeType)
        });

        this.Translate(binary.Right);
        this._sql.Append(')');
    }

    private void TranslateConstant(ConstantExpression constant)
        => this.TranslateConstant(constant.Value);

    private void TranslateConstant(object? value)
    {
        switch (value)
        {
            case byte v:
                this._sql.Append(v);
                return;
            case short v:
                this._sql.Append(v);
                return;
            case int v:
                this._sql.Append(v);
                return;
            case long v:
                this._sql.Append(v);
                return;

            case float v:
                this._sql.Append(v);
                return;
            case double v:
                this._sql.Append(v);
                return;

            case string v:
                this._sql.Append('"').Append(v.Replace(@"\", @"\\").Replace("\"", "\\\"")).Append('"');
                return;
            case bool v:
                this._sql.Append(v ? "true" : "false");
                return;
            case Guid v:
                this._sql.Append('"').Append(v.ToString()).Append('"');
                return;

            case DateTimeOffset v:
                // Cosmos doesn't support DateTimeOffset with non-zero offset, so we convert it to UTC.
                // See https://github.com/dotnet/efcore/issues/35310
                this._sql
                    .Append('"')
                    .Append(v.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.FFFFFF", CultureInfo.InvariantCulture))
                    .Append("Z\"");
                return;

            case DateTime v:
                this._sql
                    .Append('"')
                    .Append(v.ToString("yyyy-MM-ddTHH:mm:ss.FFFFFF", CultureInfo.InvariantCulture))
                    .Append('"');
                return;

#if NET
            case DateOnly v:
                this._sql
                    .Append('"')
                    .Append(v.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture))
                    .Append('"');
                return;
#endif

            case IEnumerable v when v.GetType() is var type && (type.IsArray || type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>)):
                this._sql.Append('[');

                var i = 0;
                foreach (var element in v)
                {
                    if (i++ > 0)
                    {
                        this._sql.Append(',');
                    }

                    this.TranslateConstant(element);
                }

                this._sql.Append(']');
                return;

            case null:
                this._sql.Append("null");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression)
    {
        if (this.TryBindProperty(memberExpression, out var property))
        {
            this.GeneratePropertyAccess(property);
            return;
        }

        throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
    }

    private void TranslateNewArray(NewArrayExpression newArray)
    {
        this._sql.Append('[');

        for (var i = 0; i < newArray.Expressions.Count; i++)
        {
            if (i > 0)
            {
                this._sql.Append(", ");
            }

            this.Translate(newArray.Expressions[i]);
        }

        this._sql.Append(']');
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
        // Dictionary access for dynamic mapping (r => r["SomeString"] == "foo")
        if (this.TryBindProperty(methodCall, out var property))
        {
            this.GeneratePropertyAccess(property);
            return;
        }

        switch (methodCall)
        {
            // Enumerable.Contains(), List.Contains(), MemoryExtensions.Contains()
            case var _ when TryMatchContains(methodCall, out var source, out var item):
                this.TranslateContains(source, item);
                return;

            // Enumerable.Any() with a Contains predicate (r => r.Strings.Any(s => array.Contains(s)))
            case { Method.Name: nameof(Enumerable.Any), Arguments: [var anySource, LambdaExpression lambda] } any
                when any.Method.DeclaringType == typeof(Enumerable):
                this.TranslateAny(anySource, lambda);
                return;

            default:
                throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}");
        }
    }

    private void TranslateContains(Expression source, Expression item)
    {
        this._sql.Append("ARRAY_CONTAINS(");
        this.Translate(source);
        this._sql.Append(", ");
        this.Translate(item);
        this._sql.Append(')');
    }

    /// <summary>
    /// Translates an Any() call with a Contains predicate, e.g. r.Strings.Any(s => array.Contains(s)).
    /// This checks whether any element in the array field is contained in the given values.
    /// </summary>
    private void TranslateAny(Expression source, LambdaExpression lambda)
    {
        // We only support the pattern: r.ArrayField.Any(x => values.Contains(x))
        // Translates to: EXISTS(SELECT VALUE t FROM t IN c["Field"] WHERE ARRAY_CONTAINS(@values, t))
        if (!this.TryBindProperty(source, out var property)
            || lambda.Body is not MethodCallExpression containsCall
            || !TryMatchContains(containsCall, out var valuesExpression, out var itemExpression))
        {
            throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }

        // Verify that the item is the lambda parameter
        if (itemExpression != lambda.Parameters[0])
        {
            throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }

        // Now extract the values from valuesExpression
        // Generate: EXISTS(SELECT VALUE t FROM t IN c["Field"] WHERE ARRAY_CONTAINS(@values, t))
        switch (valuesExpression)
        {
            // Inline array: r.Strings.Any(s => new[] { "a", "b" }.Contains(s))
            case NewArrayExpression newArray:
            {
                var values = new object?[newArray.Expressions.Count];
                for (var i = 0; i < newArray.Expressions.Count; i++)
                {
                    values[i] = newArray.Expressions[i] switch
                    {
                        ConstantExpression { Value: var v } => v,
                        QueryParameterExpression { Value: var v } => v,
                        _ => throw new NotSupportedException("Unsupported method call: Enumerable.Any")
                    };
                }

                this.GenerateAnyContains(property, values);
                return;
            }

            // Captured/parameterized array or list: r.Strings.Any(s => capturedArray.Contains(s))
            case QueryParameterExpression queryParameter:
                this.GenerateAnyContains(property, queryParameter);
                return;

            // Constant array: shouldn't normally happen, but handle it
            case ConstantExpression { Value: var value }:
                this.GenerateAnyContains(property, value);
                return;

            default:
                throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }
    }

    private void GenerateAnyContains(PropertyModel property, object? values)
    {
        this._sql.Append("EXISTS(SELECT VALUE t FROM t IN ");
        this.GeneratePropertyAccess(property);
        this._sql.Append(" WHERE ARRAY_CONTAINS(");
        this.TranslateConstant(values);
        this._sql.Append(", t))");
    }

    private void GenerateAnyContains(PropertyModel property, QueryParameterExpression queryParameter)
    {
        this._sql.Append("EXISTS(SELECT VALUE t FROM t IN ");
        this.GeneratePropertyAccess(property);
        this._sql.Append(" WHERE ARRAY_CONTAINS(");
        this.TranslateQueryParameter(queryParameter.Name, queryParameter.Value);
        this._sql.Append(", t))");
    }

    private void TranslateUnary(UnaryExpression unary)
    {
        switch (unary.NodeType)
        {
            // Special handling for !(a == b) and !(a != b)
            case ExpressionType.Not:
                if (unary.Operand is BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary)
                {
                    this.TranslateBinary(
                        Expression.MakeBinary(
                            binary.NodeType is ExpressionType.Equal ? ExpressionType.NotEqual : ExpressionType.Equal,
                            binary.Left,
                            binary.Right));
                    return;
                }

                this._sql.Append("(NOT ");
                this.Translate(unary.Operand);
                this._sql.Append(')');
                return;

            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            case ExpressionType.Convert when Nullable.GetUnderlyingType(unary.Type) == unary.Operand.Type:
                this.Translate(unary.Operand);
                return;

            // Handle convert over member access, for dynamic dictionary access (r => (int)r["SomeInt"] == 8)
            case ExpressionType.Convert when this.TryBindProperty(unary.Operand, out var property) && unary.Type == property.Type:
                this.GeneratePropertyAccess(property);
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }

    protected void TranslateQueryParameter(string name, object? value)
    {
        name = '@' + name;
        this._parameters.Add(name, value);
        this._sql.Append(name);
    }

    protected virtual void GeneratePropertyAccess(PropertyModel property)
        => this._sql
            .Append(CosmosNoSqlConstants.ContainerAlias)
            .Append("[\"")
            .Append(property.StorageName.Replace(@"\", @"\\").Replace("\"", "\\\""))
            .Append("\"]");
}
