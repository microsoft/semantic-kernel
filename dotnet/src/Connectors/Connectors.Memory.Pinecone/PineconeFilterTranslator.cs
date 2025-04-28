// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.ConnectorSupport.Filter;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

// This class is a modification of MongoDBFilterTranslator that uses the same query language
// (https://docs.pinecone.io/guides/data/understanding-metadata#metadata-query-language),
// with the difference of representing everything as Metadata rather than BsonDocument.
// For representing collections of any kinds, we use List<MetadataValue>,
// as we sometimes need to extend the collection (with for example another condition).
internal class PineconeFilterTranslator
{
    private VectorStoreRecordModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    internal Metadata Translate(LambdaExpression lambdaExpression, VectorStoreRecordModel model)
    {
        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { InlineCapturedVariables = true };
        var preprocessedExpression = preprocessor.Visit(lambdaExpression.Body);

        return this.Translate(preprocessedExpression);
    }

    private Metadata Translate(Expression? node)
        => node switch
        {
            BinaryExpression
            {
                NodeType: ExpressionType.Equal or ExpressionType.NotEqual
                or ExpressionType.GreaterThan or ExpressionType.GreaterThanOrEqual
                or ExpressionType.LessThan or ExpressionType.LessThanOrEqual
            } binary
            => this.TranslateEqualityComparison(binary),

            BinaryExpression { NodeType: ExpressionType.AndAlso or ExpressionType.OrElse } andOr
                => this.TranslateAndOr(andOr),
            UnaryExpression { NodeType: ExpressionType.Not } not
                => this.TranslateNot(not),

            // Special handling for bool constant as the filter expression (r => r.Bool)
            Expression when node.Type == typeof(bool) && this.TryBindProperty(node, out var property)
                => this.GenerateEqualityComparison(property, true, ExpressionType.Equal),

            MethodCallExpression methodCall => this.TranslateMethodCall(methodCall),

            _ => throw new NotSupportedException("The following NodeType is unsupported: " + node?.NodeType)
        };

    private Metadata TranslateEqualityComparison(BinaryExpression binary)
        => this.TryBindProperty(binary.Left, out var property) && binary.Right is ConstantExpression { Value: var rightConstant }
            ? this.GenerateEqualityComparison(property, rightConstant, binary.NodeType)
            : this.TryBindProperty(binary.Right, out property) && binary.Left is ConstantExpression { Value: var leftConstant }
                ? this.GenerateEqualityComparison(property, leftConstant, binary.NodeType)
                : throw new NotSupportedException("Invalid equality/comparison");

    private Metadata GenerateEqualityComparison(VectorStoreRecordPropertyModel property, object? value, ExpressionType nodeType)
    {
        if (value is null)
        {
            throw new NotSupportedException("Pincone does not support null checks in vector search pre-filters");
        }

        // Short form of equality (instead of $eq)
        if (nodeType is ExpressionType.Equal)
        {
            return new Metadata { [property.StorageName] = ToMetadata(value) };
        }

        var filterOperator = nodeType switch
        {
            ExpressionType.NotEqual => "$ne",
            ExpressionType.GreaterThan => "$gt",
            ExpressionType.GreaterThanOrEqual => "$gte",
            ExpressionType.LessThan => "$lt",
            ExpressionType.LessThanOrEqual => "$lte",

            _ => throw new UnreachableException()
        };

        return new Metadata { [property.StorageName] = new Metadata { [filterOperator] = ToMetadata(value) } };
    }

    private Metadata TranslateAndOr(BinaryExpression andOr)
    {
        var mongoOperator = andOr.NodeType switch
        {
            ExpressionType.AndAlso => "$and",
            ExpressionType.OrElse => "$or",
            _ => throw new UnreachableException()
        };

        var (left, right) = (this.Translate(andOr.Left), this.Translate(andOr.Right));

        List<MetadataValue?>? nestedLeft = GetListOrNull(left, mongoOperator);
        List<MetadataValue?>? nestedRight = GetListOrNull(right, mongoOperator);

        switch ((nestedLeft, nestedRight))
        {
            case (not null, not null):
                nestedLeft.AddRange(nestedRight);
                return left;
            case (not null, null):
                nestedLeft.Add(right);
                return left;
            case (null, not null):
                nestedRight.Insert(0, left);
                return right;
            case (null, null):
                return new Metadata { [mongoOperator] = new MetadataValue(new List<MetadataValue?> { left, right }) };
        }
    }

    private Metadata TranslateNot(UnaryExpression not)
    {
        switch (not.Operand)
        {
            // Special handling for !(a == b) and !(a != b)
            case BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary:
                return this.TranslateEqualityComparison(
                    Expression.MakeBinary(
                        binary.NodeType is ExpressionType.Equal ? ExpressionType.NotEqual : ExpressionType.Equal,
                        binary.Left,
                        binary.Right));

            // Not over bool field (Filter => r => !r.Bool)
            case Expression when not.Operand.Type == typeof(bool) && this.TryBindProperty(not.Operand, out var property):
                return this.GenerateEqualityComparison(property, false, ExpressionType.Equal);
        }

        var operand = this.Translate(not.Operand);

        // Identify NOT over $in, transform to $nin (https://www.mongodb.com/docs/manual/reference/operator/query/nin/#mongodb-query-op.-nin)
        if (operand.Count == 1 && operand.First() is { Key: var fieldName, Value: MetadataValue nested } && nested.Value is Metadata nestedMetadata
            && GetListOrNull(nestedMetadata, "$in") is List<MetadataValue> values)
        {
            return new Metadata { [fieldName] = new Metadata { ["$nin"] = values } };
        }

        throw new NotSupportedException("Pinecone does not support the NOT operator in vector search pre-filters");
    }

    private Metadata TranslateMethodCall(MethodCallExpression methodCall)
        => methodCall switch
        {
            // Enumerable.Contains()
            { Method.Name: nameof(Enumerable.Contains), Arguments: [var source, var item] } contains
                when contains.Method.DeclaringType == typeof(Enumerable)
                => this.TranslateContains(source, item),

            // List.Contains()
            {
                Method:
                {
                    Name: nameof(Enumerable.Contains),
                    DeclaringType: { IsGenericType: true } declaringType
                },
                Object: Expression source,
                Arguments: [var item]
            } when declaringType.GetGenericTypeDefinition() == typeof(List<>) => this.TranslateContains(source, item),

            _ => throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}")
        };

    private Metadata TranslateContains(Expression source, Expression item)
    {
        switch (source)
        {
            // Contains over array column (r => r.Strings.Contains("foo"))
            case var _ when this.TryBindProperty(source, out _):
                throw new NotSupportedException("Pinecone does not support Contains within array fields ($elemMatch) in vector search pre-filters");

            // Contains over inline enumerable
            case NewArrayExpression newArray:
                var elements = new object?[newArray.Expressions.Count];

                for (var i = 0; i < newArray.Expressions.Count; i++)
                {
                    if (newArray.Expressions[i] is not ConstantExpression { Value: var elementValue })
                    {
                        throw new NotSupportedException("Invalid element in array");
                    }

                    elements[i] = elementValue;
                }

                return ProcessInlineEnumerable(elements, item);

            case ConstantExpression { Value: IEnumerable enumerable and not string }:
                return ProcessInlineEnumerable(enumerable, item);

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }

        Metadata ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            if (!this.TryBindProperty(item, out var property))
            {
                throw new NotSupportedException("Unsupported item type in Contains");
            }

            return new Metadata
            {
                [property.StorageName] = new Metadata
                {
                    ["$in"] = new MetadataValue(elements.Cast<object>().Select(ToMetadata).ToList())
                }
            };
        }
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

    private static MetadataValue? ToMetadata(object? value)
        => value is null ? null : PineconeVectorStoreRecordFieldMapping.ConvertToMetadataValue(value);

    private static List<MetadataValue?>? GetListOrNull(Metadata value, string mongoOperator)
        => value.Count == 1 && value.First() is var element && element.Key == mongoOperator ? element.Value?.Value as List<MetadataValue?> : null;
}
