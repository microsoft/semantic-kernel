// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors;

#pragma warning disable MEVD9001 // Microsoft.Extensions.VectorData experimental connector-facing APIs

internal abstract class SqlFilterTranslator
{
    private readonly CollectionModel _model;
    private readonly LambdaExpression _lambdaExpression;
    private readonly ParameterExpression _recordParameter;
    protected readonly StringBuilder _sql;

    internal SqlFilterTranslator(
        CollectionModel model,
        LambdaExpression lambdaExpression,
        StringBuilder? sql = null)
    {
        this._model = model;
        this._lambdaExpression = lambdaExpression;
        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];
        this._sql = sql ?? new();
    }

    internal StringBuilder Clause => this._sql;

    internal void Translate(bool appendWhere)
    {
        if (appendWhere)
        {
            this._sql.Append("WHERE ");
        }

        var preprocessor = new FilterTranslationPreprocessor { SupportsParameterization = true };
        var preprocessedExpression = preprocessor.Preprocess(this._lambdaExpression.Body);

        this.Translate(preprocessedExpression, isSearchCondition: true);
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
        switch (methodCall)
        {
            // Dictionary access for dynamic mapping (r => r["SomeString"] == "foo")
            case MethodCallExpression when this.TryBindProperty(methodCall, out var property):
                this.GenerateColumn(property, isSearchCondition);
                return;

            // Enumerable.Contains()
            case { Method.Name: nameof(Enumerable.Contains), Arguments: [var source, var item] } contains
                when contains.Method.DeclaringType == typeof(Enumerable):
                this.TranslateContains(source, item);
                return;

            // List.Contains()
            case
            {
                Method:
                {
                    Name: nameof(Enumerable.Contains),
                    DeclaringType: { IsGenericType: true } declaringType
                },
                Object: Expression source,
                Arguments: [var item]
            } when declaringType.GetGenericTypeDefinition() == typeof(List<>):
                this.TranslateContains(source, item);
                return;

            // C# 14 made changes to overload resolution to prefer Span-based overloads when those exist ("first-class spans");
            // this makes MemoryExtensions.Contains() be resolved rather than Enumerable.Contains() (see above).
            // MemoryExtensions.Contains() also accepts a Span argument for the source, adding an implicit cast we need to remove.
            // See https://github.com/dotnet/runtime/issues/109757 for more context.
            // Note that MemoryExtensions.Contains has an optional 3rd ComparisonType parameter; we only match when
            // it's null.
            case { Method.Name: nameof(MemoryExtensions.Contains), Arguments: [var spanArg, var item, ..] } contains
                when contains.Method.DeclaringType == typeof(MemoryExtensions)
                    && (contains.Arguments.Count is 2
                        || (contains.Arguments.Count is 3 && contains.Arguments[2] is ConstantExpression { Value: null }))
                    && TryUnwrapSpanImplicitCast(spanArg, out var source):
                this.TranslateContains(source, item);
                return;

            // Enumerable.Any() with a Contains predicate (r => r.Strings.Any(s => array.Contains(s)))
            case { Method.Name: nameof(Enumerable.Any), Arguments: [var source, LambdaExpression lambda] } any
                when any.Method.DeclaringType == typeof(Enumerable):
                this.TranslateAny(source, lambda);
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
            || lambda.Body is not MethodCallExpression containsCall)
        {
            throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }

        // Match Enumerable.Contains(source, item), List<T>.Contains(item), or MemoryExtensions.Contains
        var (valuesExpression, itemExpression) = containsCall switch
        {
            // Enumerable.Contains(source, item)
            { Method.Name: nameof(Enumerable.Contains), Arguments: [var src, var item] }
                when containsCall.Method.DeclaringType == typeof(Enumerable)
                => (src, item),

            // List<T>.Contains(item)
            { Method: { Name: nameof(Enumerable.Contains), DeclaringType: { IsGenericType: true } declaringType }, Object: Expression src, Arguments: [var item] }
                when declaringType.GetGenericTypeDefinition() == typeof(List<>)
                => (src, item),

            // MemoryExtensions.Contains (C# 14 first-class spans)
            { Method.Name: nameof(MemoryExtensions.Contains), Arguments: [var spanArg, var item, ..] }
                when containsCall.Method.DeclaringType == typeof(MemoryExtensions)
                    && (containsCall.Arguments.Count is 2
                        || (containsCall.Arguments.Count is 3 && containsCall.Arguments[2] is ConstantExpression { Value: null }))
                    && TryUnwrapSpanImplicitCast(spanArg, out var unwrappedSource)
                => (unwrappedSource, item),

            _ => throw new NotSupportedException("Unsupported method call: Enumerable.Any")
        };

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

    private bool TryBindProperty(Expression expression, [NotNullWhen(true)] out PropertyModel? property)
    {
        var unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            unwrappedExpression = convert.Operand;
        }

        var modelName = unwrappedExpression switch
        {
            // Regular member access for strongly-typed POCO binding (e.g. r => r.SomeInt == 8)
            MemberExpression memberExpression when memberExpression.Expression == this._recordParameter
                => memberExpression.Member.Name,

            // Dictionary lookup for weakly-typed dynamic binding (e.g. r => r["SomeInt"] == 8)
            MethodCallExpression
            {
                Method: { Name: "get_Item", DeclaringType: var declaringType },
                Arguments: [ConstantExpression { Value: string keyName }]
            } methodCall when methodCall.Object == this._recordParameter && declaringType == typeof(Dictionary<string, object?>)
                => keyName,

            _ => null
        };

        if (modelName is null)
        {
            property = null;
            return false;
        }

        if (!this._model.PropertyMap.TryGetValue(modelName, out property))
        {
            throw new InvalidOperationException($"Property name '{modelName}' provided as part of the filter clause is not a valid property name.");
        }

        // Now that we have the property, go over all wrapping Convert nodes again to ensure that they're compatible with the property type
        var unwrappedPropertyType = Nullable.GetUnderlyingType(property.Type) ?? property.Type;
        unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            var convertType = Nullable.GetUnderlyingType(convert.Type) ?? convert.Type;
            if (convertType != unwrappedPropertyType && convertType != typeof(object))
            {
                throw new InvalidCastException($"Property '{property.ModelName}' is being cast to type '{convert.Type.Name}', but its configured type is '{property.Type.Name}'.");
            }

            unwrappedExpression = convert.Operand;
        }

        return true;
    }

    protected static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
    {
        // Different versions of the compiler seem to generate slightly different expression tree representations for this
        // implicit cast:
        var (unwrapped, castDeclaringType) = expression switch
        {
            UnaryExpression
            {
                NodeType: ExpressionType.Convert,
                Method: { Name: "op_Implicit", DeclaringType: { IsGenericType: true } implicitCastDeclaringType },
                Operand: var operand
            } => (operand, implicitCastDeclaringType),

            MethodCallExpression
            {
                Method: { Name: "op_Implicit", DeclaringType: { IsGenericType: true } implicitCastDeclaringType },
                Arguments: [var firstArgument]
            } => (firstArgument, implicitCastDeclaringType),

            // After the preprocessor runs, the Convert node may have Method: null because the visitor
            // recreates the UnaryExpression with a different operand type (QueryParameterExpression).
            // Handle this case by checking if the target type is Span<T> or ReadOnlySpan<T>.
            UnaryExpression
            {
                NodeType: ExpressionType.Convert,
                Method: null,
                Type: { IsGenericType: true } targetType,
                Operand: var operand
            } when targetType.GetGenericTypeDefinition() is var gtd
                && (gtd == typeof(Span<>) || gtd == typeof(ReadOnlySpan<>))
                => (operand, targetType),

            _ => (null, null)
        };

        // For the dynamic case, there's a Convert node representing an up-cast to object[]; unwrap that too.
        // Also handle cases where the preprocessor adds a Convert node back to the array type.
        while (unwrapped is UnaryExpression
            {
                NodeType: ExpressionType.Convert,
                Method: null,
                Operand: var innerOperand
            })
        {
            unwrapped = innerOperand;
        }

        if (unwrapped is not null
            && castDeclaringType?.GetGenericTypeDefinition() is var genericTypeDefinition
                && (genericTypeDefinition == typeof(Span<>) || genericTypeDefinition == typeof(ReadOnlySpan<>)))
        {
            result = unwrapped;
            return true;
        }

        result = null;
        return false;
    }
}
