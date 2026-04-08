// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors;

#pragma warning disable MEVD9001 // Microsoft.Extensions.VectorData experimental connector-facing APIs

internal abstract class SqlFilterTranslator : FilterTranslatorBase
{
    protected readonly StringBuilder _sql;
    private readonly Expression _preprocessedExpression;

    internal SqlFilterTranslator(
        CollectionModel model,
        LambdaExpression lambdaExpression,
        StringBuilder? sql = null)
    {
        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._sql = sql ?? new();

        this._preprocessedExpression = this.PreprocessFilter(lambdaExpression, model, new FilterPreprocessingOptions { SupportsParameterization = true });
    }

    internal StringBuilder Clause => this._sql;

    internal void Translate(bool appendWhere)
    {
        if (appendWhere)
        {
            this._sql.Append("WHERE ");
        }

        this.Translate(this._preprocessedExpression, isSearchCondition: true);
    }

    protected void Translate(Expression? node, bool isSearchCondition = false)
    {
        switch (node)
        {
            case BinaryExpression binary:
                this.TranslateBinary(binary);
                return;

            case ConstantExpression constant:
                this.TranslateConstant(constant.Value, isSearchCondition);
                return;

            case QueryParameterExpression { Name: var name, Value: var value }:
                this.TranslateQueryParameter(value);
                return;

            case MemberExpression member:
                this.TranslateMember(member, isSearchCondition);
                return;

            case MethodCallExpression methodCall:
                this.TranslateMethodCall(methodCall, isSearchCondition);
                return;

            case UnaryExpression unary:
                this.TranslateUnary(unary, isSearchCondition);
                return;

            default:
                throw new NotSupportedException("Unsupported NodeType in filter: " + node?.NodeType);
        }
    }

    protected void TranslateBinary(BinaryExpression binary)
    {
        // Special handling for null comparisons
        switch (binary.NodeType)
        {
            case ExpressionType.Equal when IsNull(binary.Right):
                this._sql.Append('(');
                this.Translate(binary.Left);
                this._sql.Append(" IS NULL)");
                return;
            case ExpressionType.NotEqual when IsNull(binary.Right):
                this._sql.Append('(');
                this.Translate(binary.Left);
                this._sql.Append(" IS NOT NULL)");
                return;

            case ExpressionType.Equal when IsNull(binary.Left):
                this._sql.Append('(');
                this.Translate(binary.Right);
                this._sql.Append(" IS NULL)");
                return;
            case ExpressionType.NotEqual when IsNull(binary.Left):
                this._sql.Append('(');
                this.Translate(binary.Right);
                this._sql.Append(" IS NOT NULL)");
                return;
        }

        this._sql.Append('(');
        this.Translate(binary.Left, isSearchCondition: binary.NodeType is ExpressionType.AndAlso or ExpressionType.OrElse);

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

        this.Translate(binary.Right, isSearchCondition: binary.NodeType is ExpressionType.AndAlso or ExpressionType.OrElse);

        this._sql.Append(')');

        static bool IsNull(Expression expression)
            => expression is ConstantExpression { Value: null } or QueryParameterExpression { Value: null };
    }

    protected virtual void TranslateConstant(object? value, bool isSearchCondition)
    {
        switch (value)
        {
            case byte b:
                this._sql.Append(b);
                return;
            case short s:
                this._sql.Append(s);
                return;
            case int i:
                this._sql.Append(i);
                return;
            case long l:
                this._sql.Append(l);
                return;

            case float f:
                this._sql.Append(f);
                return;
            case double d:
                this._sql.Append(d);
                return;
            case decimal d:
                this._sql.Append(d);
                return;

            case string untrustedInput:
                // This is the only place where we allow untrusted input to be passed in, so we need to quote and escape it.
                // Luckily for us, values are escaped in the same way for every provider that we support so far.
                this._sql.Append('\'').Append(untrustedInput.Replace("'", "''")).Append('\'');
                return;
            case bool b:
                this._sql.Append(b ? "TRUE" : "FALSE");
                return;
            case Guid g:
                this._sql.Append('\'').Append(g.ToString()).Append('\'');
                return;

            case DateTime dateTime:
            case DateTimeOffset dateTimeOffset:
            case Array:
#if NET
            case DateOnly dateOnly:
            case TimeOnly timeOnly:
#endif
                throw new UnreachableException("Database-specific format, needs to be implemented in the provider's derived translator.");

            case null:
                this._sql.Append("NULL");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression, bool isSearchCondition)
    {
        if (this.TryBindProperty(memberExpression, out var property))
        {
            this.GenerateColumn(property, isSearchCondition);
            return;
        }

        throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
    }

    protected virtual void GenerateColumn(PropertyModel property, bool isSearchCondition = false)
        // StorageName is considered to be a safe input, we quote and escape it mostly to produce valid SQL.
        => this._sql.Append('"').Append(property.StorageName.Replace("\"", "\"\"")).Append('"');

    protected abstract void TranslateQueryParameter(object? value);

    private void TranslateMethodCall(MethodCallExpression methodCall, bool isSearchCondition = false)
    {
        // Dictionary access for dynamic mapping (r => r["SomeString"] == "foo")
        if (this.TryBindProperty(methodCall, out var property))
        {
            this.GenerateColumn(property, isSearchCondition);
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
        switch (source)
        {
            // Contains over array column (r => r.Strings.Contains("foo"))
            case var _ when this.TryBindProperty(source, out _):
                this.TranslateContainsOverArrayColumn(source, item);
                return;

            // Contains over inline array (r => new[] { "foo", "bar" }.Contains(r.String))
            case NewArrayExpression newArray:
                this.Translate(item);
                this._sql.Append(" IN (");

                var isFirst = true;
                foreach (var element in newArray.Expressions)
                {
                    if (isFirst)
                    {
                        isFirst = false;
                    }
                    else
                    {
                        this._sql.Append(", ");
                    }

                    this.Translate(element);
                }

                this._sql.Append(')');
                return;

            // Contains over captured array (r => arrayLocalVariable.Contains(r.String))
            case QueryParameterExpression { Value: var value }:
                this.TranslateContainsOverParameterizedArray(source, item, value);
                return;

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }
    }

    protected abstract void TranslateContainsOverArrayColumn(Expression source, Expression item);

    protected abstract void TranslateContainsOverParameterizedArray(Expression source, Expression item, object? value);

    /// <summary>
    /// Translates an Any() call with a Contains predicate, e.g. r.Strings.Any(s => array.Contains(s)).
    /// This checks whether any element in the array column is contained in the given values.
    /// </summary>
    private void TranslateAny(Expression source, LambdaExpression lambda)
    {
        // We only support the pattern: r.ArrayColumn.Any(x => values.Contains(x))
        // where 'values' is an inline array, captured array, or captured list.
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

                this.TranslateAnyContainsOverArrayColumn(property, values);
                return;
            }

            // Captured/parameterized array or list: r.Strings.Any(s => capturedArray.Contains(s))
            case QueryParameterExpression { Value: var value }:
                this.TranslateAnyContainsOverArrayColumn(property, value);
                return;

            // Constant array: shouldn't normally happen, but handle it
            case ConstantExpression { Value: var value }:
                this.TranslateAnyContainsOverArrayColumn(property, value);
                return;

            default:
                throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }
    }

    protected abstract void TranslateAnyContainsOverArrayColumn(PropertyModel property, object? values);

    private void TranslateUnary(UnaryExpression unary, bool isSearchCondition)
    {
        switch (unary.NodeType)
        {
            case ExpressionType.Not:
                // Special handling for !(a == b) and !(a != b)
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
                this.Translate(unary.Operand, isSearchCondition);
                this._sql.Append(')');
                return;

            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            case ExpressionType.Convert when Nullable.GetUnderlyingType(unary.Type) == unary.Operand.Type:
                this.Translate(unary.Operand, isSearchCondition);
                return;

            // Handle convert over member access, for dynamic dictionary access (r => (int)r["SomeInt"] == 8)
            case ExpressionType.Convert when this.TryBindProperty(unary.Operand, out var property) && unary.Type == property.Type:
                this.GenerateColumn(property, isSearchCondition);
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }
}
