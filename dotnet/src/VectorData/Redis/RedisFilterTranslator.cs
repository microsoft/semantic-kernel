// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors.Redis;

internal class RedisFilterTranslator
{
    private CollectionModel _model = null!;
    private ParameterExpression _recordParameter = null!;
    private readonly StringBuilder _filter = new();

    internal string Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        Debug.Assert(this._filter.Length == 0);

        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        // Redis doesn't seem to have a native way of expressing "always true" filters; since this scenario is important for fetching
        // all records (via GetAsync with filter), we special-case and support it here. Note that false isn't supported (useless),
        // nor is 'x && true'.
        if (lambdaExpression.Body is ConstantExpression { Value: true })
        {
            return "*";
        }

        var preprocessor = new FilterTranslationPreprocessor { SupportsParameterization = false };
        var preprocessedExpression = preprocessor.Preprocess(lambdaExpression.Body);

        this.Translate(preprocessedExpression);
        return this._filter.ToString();
    }

    private void Translate(Expression? node)
    {
        switch (node)
        {
            case BinaryExpression
            {
                NodeType: ExpressionType.Equal or ExpressionType.NotEqual
                or ExpressionType.GreaterThan or ExpressionType.GreaterThanOrEqual
                or ExpressionType.LessThan or ExpressionType.LessThanOrEqual
            } binary:
                this.TranslateEqualityComparison(binary);
                return;

            case BinaryExpression { NodeType: ExpressionType.AndAlso } andAlso:
                // https://redis.io/docs/latest/develop/interact/search-and-query/query/combined/#and
                this._filter.Append('(');
                this.Translate(andAlso.Left);
                this._filter.Append(' ');
                this.Translate(andAlso.Right);
                this._filter.Append(')');
                return;

            case BinaryExpression { NodeType: ExpressionType.OrElse } orElse:
                // https://redis.io/docs/latest/develop/interact/search-and-query/query/combined/#or
                this._filter.Append('(');
                this.Translate(orElse.Left);
                this._filter.Append(" | ");
                this.Translate(orElse.Right);
                this._filter.Append(')');
                return;

            case UnaryExpression { NodeType: ExpressionType.Not } not:
                this.TranslateNot(not.Operand);
                return;

            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            case UnaryExpression { NodeType: ExpressionType.Convert } convert when Nullable.GetUnderlyingType(convert.Type) == convert.Operand.Type:
                this.Translate(convert.Operand);
                return;

            // MemberExpression is generally handled within e.g. TranslateEqual; this is used to translate direct bool inside filter (e.g. Filter => r => r.Bool)
            case MemberExpression member when member.Type == typeof(bool) && this.TryBindProperty(member, out _):
            {
                this.TranslateEqualityComparison(Expression.Equal(member, Expression.Constant(true)));
                return;
            }

            case MethodCallExpression methodCall:
                this.TranslateMethodCall(methodCall);
                return;

            default:
                throw new NotSupportedException("Redis does not support the following NodeType in filters: " + node?.NodeType);
        }
    }

    private void TranslateEqualityComparison(BinaryExpression binary)
    {
        if (!TryProcessEqualityComparison(binary.Left, binary.Right) && !TryProcessEqualityComparison(binary.Right, binary.Left))
        {
            throw new NotSupportedException("Binary expression not supported by Redis");
        }

        bool TryProcessEqualityComparison(Expression first, Expression second)
        {
            if (this.TryBindProperty(first, out var property) && second is ConstantExpression { Value: var constantValue })
            {
                // Numeric negation has a special syntax (!=), for the rest we nest in a NOT
                if (binary.NodeType is ExpressionType.NotEqual && constantValue is not int or long or float or double)
                {
                    this.TranslateNot(Expression.Equal(first, second));
                    return true;
                }

                // Redis field names cannot be escaped in all contexts; storage names are validated during model building.
                // https://redis.io/docs/latest/develop/interact/search-and-query/query/exact-match
                this._filter.Append('@').Append(property.StorageName);

                this._filter.Append(
                    binary.NodeType switch
                    {
                        ExpressionType.Equal when constantValue is byte or short or int or long or float or double => $" == {constantValue}",
                        ExpressionType.Equal when constantValue is string stringValue
#if NET
                            => $$""":{"{{stringValue.Replace("\"", "\\\"", StringComparison.Ordinal)}}"}""",
#else
                            => $$""":{"{{stringValue.Replace("\"", "\"\"")}}"}""",
#endif
                        ExpressionType.Equal when constantValue is null => throw new NotSupportedException("Null value type not supported"), // TODO

                        ExpressionType.NotEqual when constantValue is int or long or float or double => $" != {constantValue}",
                        ExpressionType.NotEqual => throw new InvalidOperationException("Unreachable"), // Handled above

                        ExpressionType.GreaterThan => $" > {constantValue}",
                        ExpressionType.GreaterThanOrEqual => $" >= {constantValue}",
                        ExpressionType.LessThan => $" < {constantValue}",
                        ExpressionType.LessThanOrEqual => $" <= {constantValue}",

                        _ => throw new InvalidOperationException("Unsupported equality/comparison")
                    });

                return true;
            }

            return false;
        }
    }

    private void TranslateNot(Expression expression)
    {
        // https://redis.io/docs/latest/develop/interact/search-and-query/query/combined/#not
        this._filter.Append("(-");
        this.Translate(expression);
        this._filter.Append(')');
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
        switch (methodCall)
        {
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
        // Contains over tag field
        if (this.TryBindProperty(source, out var property) && item is ConstantExpression { Value: string stringConstant })
        {
            // Redis field names cannot be escaped in all contexts; storage names are validated during model building.
            this._filter
                .Append('@')
                .Append(property.StorageName)
                .Append(":{")
                .Append(stringConstant)
                .Append('}');
            return;
        }

        throw new NotSupportedException("Contains supported only over tag field");
    }

    /// <summary>
    /// Translates an Any() call with a Contains predicate, e.g. r.Strings.Any(s => array.Contains(s)).
    /// This checks whether any element in the array field is contained in the given values.
    /// </summary>
    private void TranslateAny(Expression source, LambdaExpression lambda)
    {
        // We only support the pattern: r.ArrayField.Any(x => values.Contains(x))
        // Translates to: @Field:{value1 | value2 | value3}
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

        // Extract the values
        IEnumerable values = valuesExpression switch
        {
            NewArrayExpression newArray => ExtractArrayValues(newArray),
            ConstantExpression { Value: IEnumerable enumerable and not string } => enumerable,
            _ => throw new NotSupportedException("Unsupported method call: Enumerable.Any")
        };

        // Generate: @Field:{value1 | value2 | value3}
        this._filter
            .Append('@')
            .Append(property.StorageName)
            .Append(":{");

        var isFirst = true;
        foreach (var element in values)
        {
            if (element is not string stringElement)
            {
                throw new NotSupportedException("Any with Contains over non-string arrays is not supported");
            }

            if (isFirst)
            {
                isFirst = false;
            }
            else
            {
                this._filter.Append(" | ");
            }

            this._filter.Append(stringElement);
        }

        this._filter.Append('}');

        static object?[] ExtractArrayValues(NewArrayExpression newArray)
        {
            var result = new object?[newArray.Expressions.Count];
            for (var i = 0; i < newArray.Expressions.Count; i++)
            {
                if (newArray.Expressions[i] is not ConstantExpression { Value: var elementValue })
                {
                    throw new NotSupportedException("Invalid element in array");
                }

                result[i] = elementValue;
            }

            return result;
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

    private static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
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
