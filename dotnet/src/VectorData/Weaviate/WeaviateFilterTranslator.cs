// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// https://weaviate.io/developers/weaviate/api/graphql/filters#filter-structure
internal class WeaviateFilterTranslator
{
    private CollectionModel _model = null!;
    private ParameterExpression _recordParameter = null!;
    private readonly StringBuilder _filter = new();

    internal string? Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        Debug.Assert(this._filter.Length == 0);

        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        // Weaviate doesn't seem to have a native way of expressing "always true" filters; since this scenario is important for fetching
        // all records (via GetAsync with filter), we special-case and support it here. Note that false isn't supported (useless),
        // nor is 'x && true'.
        if (lambdaExpression.Body is ConstantExpression { Value: true })
        {
            return null;
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
            Type t when t == typeof(DateTimeOffset) => "valueDate",

            _ => throw new NotSupportedException($"Unsupported value type {type.FullName} in filter.")
        });

        this._filter.Append(": ");

        // Value
        this._filter.Append(JsonSerializer.Serialize(value));

        this._filter.Append('}');
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

            default:
                throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}");
        }

        static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
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

                _ => (null, null)
            };

            // For the dynamic case, there's a Convert node representing an up-cast to object[]; unwrap that too.
            if (unwrapped is UnaryExpression
                {
                    NodeType: ExpressionType.Convert,
                    Method: null
                } convert
                && convert.Type == typeof(object[]))
            {
                result = convert.Operand;
                return true;
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
}
