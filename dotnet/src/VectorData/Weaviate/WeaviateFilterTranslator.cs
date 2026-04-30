// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable MEVD9001 // Experimental: filter translation base types

// https://weaviate.io/developers/weaviate/api/graphql/filters#filter-structure
internal class WeaviateFilterTranslator : FilterTranslatorBase
{
    private readonly StringBuilder _filter = new();

    internal string? Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        // Weaviate doesn't seem to have a native way of expressing "always true" filters; since this scenario is important for fetching
        // all records (via GetAsync with filter), we special-case and support it here. Note that false isn't supported (useless),
        // nor is 'x && true'.
        if (lambdaExpression.Body is ConstantExpression { Value: true })
        {
            return null;
        }

        var preprocessedExpression = this.PreprocessFilter(lambdaExpression, model, new FilterPreprocessingOptions());

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
                this._filter.Append("{ operator: And, operands: [");
                this.Translate(andAlso.Left);
                this._filter.Append(", ");
                this.Translate(andAlso.Right);
                this._filter.Append("] }");
                return;

            case BinaryExpression { NodeType: ExpressionType.OrElse } orElse:
                this._filter.Append("{ operator: Or, operands: [");
                this.Translate(orElse.Left);
                this._filter.Append(", ");
                this.Translate(orElse.Right);
                this._filter.Append("] }");
                return;

            case UnaryExpression { NodeType: ExpressionType.Not } not:
            {
                switch (not.Operand)
                {
                    // Special handling for !(a == b) and !(a != b), transforming to a != b and a == b respectively.
                    case BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary:
                        this.TranslateEqualityComparison(
                            Expression.MakeBinary(
                                binary.NodeType is ExpressionType.Equal ? ExpressionType.NotEqual : ExpressionType.Equal,
                                binary.Left,
                                binary.Right));
                        return;

                    // Not over bool field (r => !r.Bool)
                    case var negated when negated.Type == typeof(bool) && this.TryBindProperty(negated, out var property):
                        this.GenerateEqualityComparison(property.StorageName, false, ExpressionType.Equal);
                        return;

                    default:
                        throw new NotSupportedException("Weaviate does not support the NOT operator (see https://github.com/weaviate/weaviate/issues/3683)");
                }
            }

            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            case UnaryExpression { NodeType: ExpressionType.Convert } convert when Nullable.GetUnderlyingType(convert.Type) == convert.Operand.Type:
                this.Translate(convert.Operand);
                return;

            // Special handling for bool constant as the filter expression (r => r.Bool)
            case Expression when node.Type == typeof(bool) && this.TryBindProperty(node, out var property):
                this.GenerateEqualityComparison(property.StorageName, true, ExpressionType.Equal);
                return;

            case MethodCallExpression methodCall:
                this.TranslateMethodCall(methodCall);
                return;

            default:
                throw new NotSupportedException("The following NodeType is unsupported: " + node?.NodeType);
        }
    }

    private void TranslateEqualityComparison(BinaryExpression binary)
    {
        if (this.TryBindProperty(binary.Left, out var property) && binary.Right is ConstantExpression { Value: var rightConstant })
        {
            this.GenerateEqualityComparison(property.StorageName, rightConstant, binary.NodeType);
            return;
        }

        if (this.TryBindProperty(binary.Right, out property) && binary.Left is ConstantExpression { Value: var leftConstant })
        {
            this.GenerateEqualityComparison(property.StorageName, leftConstant, binary.NodeType);
            return;
        }

        throw new NotSupportedException("Invalid equality/comparison");
    }

    private void GenerateEqualityComparison(string propertyStorageName, object? value, ExpressionType nodeType)
    {
        // { path: ["intPropName"], operator: Equal, ValueInt: 8 }
        this._filter
            .Append("{ path: [\"")
            .Append(JsonEncodedText.Encode(propertyStorageName))
            .Append("\"], operator: ");

        // Special handling for null comparisons
        if (value is null)
        {
            if (nodeType is ExpressionType.Equal or ExpressionType.NotEqual)
            {
                this._filter
                    .Append("IsNull, valueBoolean: ")
                    .Append(nodeType is ExpressionType.Equal ? "true" : "false")
                    .Append(" }");
                return;
            }

            throw new NotSupportedException("null value supported only with equality/inequality checks");
        }

        // Operator
        this._filter.Append(nodeType switch
        {
            ExpressionType.Equal => "Equal",
            ExpressionType.NotEqual => "NotEqual",

            ExpressionType.GreaterThan => "GreaterThan",
            ExpressionType.GreaterThanOrEqual => "GreaterThanEqual",
            ExpressionType.LessThan => "LessThan",
            ExpressionType.LessThanOrEqual => "LessThanEqual",

            _ => throw new UnreachableException()
        });

        this._filter.Append(", ");

        // FieldType
        var type = value.GetType();
        if (Nullable.GetUnderlyingType(type) is Type underlying)
        {
            type = underlying;
        }

        this._filter.Append(value.GetType() switch
        {
            Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) => "valueInt",
            Type t when t == typeof(bool) => "valueBoolean",
            Type t when t == typeof(string) || t == typeof(Guid) => "valueText",
            Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) => "valueNumber",
            Type t when t == typeof(DateTime) => "valueDate",
            Type t when t == typeof(DateTimeOffset) => "valueDate",
#if NET
            Type t when t == typeof(DateOnly) => "valueDate",
#endif

            _ => throw new NotSupportedException($"Unsupported value type {type.FullName} in filter.")
        });

        this._filter.Append(": ");

        // Value — use Weaviate's JSON serializer options for proper date/time formatting
        this._filter.Append(JsonSerializer.Serialize(value, value.GetType(), WeaviateConstants.s_jsonSerializerOptions));

        this._filter.Append('}');
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
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
        // Contains over array
        // { path: ["stringArrayPropName"], operator: ContainsAny, valueText: ["foo"] }
        if (this.TryBindProperty(source, out var property) && item is ConstantExpression { Value: string stringConstant })
        {
            this._filter
                .Append("{ path: [\"")
                .Append(JsonEncodedText.Encode(property.StorageName))
                .Append("\"], operator: ContainsAny, valueText: [")
                .Append(JsonEncodedText.Encode(stringConstant))
                .Append("]}");
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
        // Translates to: { path: ["Field"], operator: ContainsAny, valueText: ["value1", "value2"] }
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

        // Extract the values
        IEnumerable values = valuesExpression switch
        {
            NewArrayExpression newArray => ExtractArrayValues(newArray),
            ConstantExpression { Value: IEnumerable enumerable and not string } => enumerable,
            _ => throw new NotSupportedException("Unsupported method call: Enumerable.Any")
        };

        // Generate: { path: ["Field"], operator: ContainsAny, valueText: ["value1", "value2"] }
        this._filter
            .Append("{ path: [\"")
            .Append(JsonEncodedText.Encode(property.StorageName))
            .Append("\"], operator: ContainsAny, valueText: [");

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
                this._filter.Append(", ");
            }

            this._filter.Append(JsonSerializer.Serialize(stringElement));
        }

        this._filter.Append("]}");

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
}
