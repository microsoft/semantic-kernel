// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.ConnectorSupport.Filter;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// https://weaviate.io/developers/weaviate/api/graphql/filters#filter-structure
internal class WeaviateFilterTranslator
{
    private VectorStoreRecordModel _model = null!;
    private ParameterExpression _recordParameter = null!;
    private readonly StringBuilder _filter = new();

    internal string Translate(LambdaExpression lambdaExpression, VectorStoreRecordModel model)
    {
        Debug.Assert(this._filter.Length == 0);

        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { InlineCapturedVariables = true };
        var preprocessedExpression = preprocessor.Visit(lambdaExpression.Body);

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

    private bool TryBindProperty(Expression expression, [NotNullWhen(true)] out VectorStoreRecordPropertyModel? property)
    {
        Type? convertedClrType = null;

        if (expression is UnaryExpression { NodeType: ExpressionType.Convert } unary)
        {
            expression = unary.Operand;
            convertedClrType = unary.Type;
        }

        var modelName = expression switch
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

        if (convertedClrType is not null && convertedClrType != property.Type)
        {
            throw new InvalidCastException($"Property '{property.ModelName}' is being cast to type '{convertedClrType.Name}', but its configured type is '{property.Type.Name}'.");
        }

        return true;
    }
}
