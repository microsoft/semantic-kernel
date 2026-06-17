// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

#pragma warning disable MEVD9001 // Experimental: filter translation base types

// MongoDB query reference: https://www.mongodb.com/docs/manual/reference/operator/query
// Information specific to vector search pre-filter: https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#atlas-vector-search-pre-filter
internal class CosmosMongoFilterTranslator : FilterTranslatorBase
{
    internal BsonDocument Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        var preprocessedExpression = this.PreprocessFilter(lambdaExpression, model, new FilterPreprocessingOptions());

        return this.Translate(preprocessedExpression);
    }

    private BsonDocument Translate(Expression? node)
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
            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            UnaryExpression { NodeType: ExpressionType.Convert } convert when Nullable.GetUnderlyingType(convert.Type) == convert.Operand.Type
                => this.Translate(convert.Operand),

            // Special handling for bool constant as the filter expression (r => r.Bool)
            Expression when node.Type == typeof(bool) && this.TryBindProperty(node, out var property)
                => this.GenerateEqualityComparison(property, value: true, ExpressionType.Equal),
            // Handle true literal (r => true), which is useful for fetching all records
            ConstantExpression { Value: true }
                => [],

            MethodCallExpression methodCall => this.TranslateMethodCall(methodCall),

            _ => throw new NotSupportedException("The following NodeType is unsupported: " + node?.NodeType)
        };

    private BsonDocument TranslateEqualityComparison(BinaryExpression binary)
        => this.TryBindProperty(binary.Left, out var property) && binary.Right is ConstantExpression { Value: var rightConstant }
            ? this.GenerateEqualityComparison(property, rightConstant, binary.NodeType)
            : this.TryBindProperty(binary.Right, out property) && binary.Left is ConstantExpression { Value: var leftConstant }
                ? this.GenerateEqualityComparison(property, leftConstant, binary.NodeType)
                : throw new NotSupportedException("Invalid equality/comparison");

    private BsonDocument GenerateEqualityComparison(PropertyModel property, object? value, ExpressionType nodeType)
    {
        if (value is null)
        {
            throw new NotSupportedException("MongogDB does not support null checks in vector search pre-filters");
        }

        // Short form of equality (instead of $eq)
        if (nodeType is ExpressionType.Equal)
        {
            return new BsonDocument { [property.StorageName] = BsonValueFactory.Create(value) };
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

        return new BsonDocument { [property.StorageName] = new BsonDocument { [filterOperator] = BsonValueFactory.Create(value) } };
    }

    private BsonDocument TranslateAndOr(BinaryExpression andOr)
    {
        var mongoOperator = andOr.NodeType switch
        {
            ExpressionType.AndAlso => "$and",
            ExpressionType.OrElse => "$or",
            _ => throw new UnreachableException()
        };

        var (left, right) = (this.Translate(andOr.Left), this.Translate(andOr.Right));

        var nestedLeft = left.ElementCount == 1 && left.Elements.First() is var leftElement && leftElement.Name == mongoOperator ? (BsonArray)leftElement.Value : null;
        var nestedRight = right.ElementCount == 1 && right.Elements.First() is var rightElement && rightElement.Name == mongoOperator ? (BsonArray)rightElement.Value : null;

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
                return new BsonDocument { [mongoOperator] = new BsonArray([left, right]) };
        }
    }

    private BsonDocument TranslateNot(UnaryExpression not)
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

            // Not over bool field (r => !r.Bool)
            case var negated when negated.Type == typeof(bool) && this.TryBindProperty(negated, out var property):
                return this.GenerateEqualityComparison(property, false, ExpressionType.Equal);
        }

        var operand = this.Translate(not.Operand);

        // Identify NOT over $in, transform to $nin (https://www.mongodb.com/docs/manual/reference/operator/query/nin/#mongodb-query-op.-nin)
        if (operand.ElementCount == 1 && operand.Elements.First() is { Name: var fieldName, Value: BsonDocument nested } &&
            nested.ElementCount == 1 && nested.Elements.First() is { Name: "$in", Value: BsonArray values })
        {
            return new BsonDocument { [fieldName] = new BsonDocument { ["$nin"] = values } };
        }

        throw new NotSupportedException("MongogDB does not support the NOT operator in vector search pre-filters");
    }

    private BsonDocument TranslateMethodCall(MethodCallExpression methodCall)
    {
        return methodCall switch
        {
            // Enumerable.Contains(), List.Contains(), MemoryExtensions.Contains()
            _ when TryMatchContains(methodCall, out var source, out var item)
                => this.TranslateContains(source, item),

            _ => throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}")
        };
    }

    private BsonDocument TranslateContains(Expression source, Expression item)
    {
        switch (source)
        {
            // Contains over array column (r => r.Strings.Contains("foo"))
            case var _ when this.TryBindProperty(source, out _):
                throw new NotSupportedException("MongoDB does not support Contains within array fields ($elemMatch) in vector search pre-filters");

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

            // Contains over captured enumerable (we inline)
            case ConstantExpression { Value: IEnumerable enumerable and not string }:
                return ProcessInlineEnumerable(enumerable, item);

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }

        BsonDocument ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            if (!this.TryBindProperty(item, out var property))
            {
                throw new NotSupportedException("Unsupported item type in Contains");
            }

            return new BsonDocument
            {
                [property.StorageName] = new BsonDocument
                {
                    ["$in"] = new BsonArray(from object? element in elements select BsonValueFactory.Create(element))
                }
            };
        }
    }
}
