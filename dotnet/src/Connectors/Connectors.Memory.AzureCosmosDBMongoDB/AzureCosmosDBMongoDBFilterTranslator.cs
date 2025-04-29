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
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

// MongoDB query reference: https://www.mongodb.com/docs/manual/reference/operator/query
// Information specific to vector search pre-filter: https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#atlas-vector-search-pre-filter
internal class AzureCosmosDBMongoDBFilterTranslator
{
    private VectorStoreRecordModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    internal BsonDocument Translate(LambdaExpression lambdaExpression, VectorStoreRecordModel model)
    {
        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { InlineCapturedVariables = true };
        var preprocessedExpression = preprocessor.Visit(lambdaExpression.Body);

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

            // Special handling for bool constant as the filter expression (r => r.Bool)
            Expression when node.Type == typeof(bool) && this.TryBindProperty(node, out var property)
                => this.GenerateEqualityComparison(property, value: true, ExpressionType.Equal),

            MethodCallExpression methodCall => this.TranslateMethodCall(methodCall),

            _ => throw new NotSupportedException("The following NodeType is unsupported: " + node?.NodeType)
        };

    private BsonDocument TranslateEqualityComparison(BinaryExpression binary)
        => this.TryBindProperty(binary.Left, out var property) && binary.Right is ConstantExpression { Value: var rightConstant }
            ? this.GenerateEqualityComparison(property, rightConstant, binary.NodeType)
            : this.TryBindProperty(binary.Right, out property) && binary.Left is ConstantExpression { Value: var leftConstant }
                ? this.GenerateEqualityComparison(property, leftConstant, binary.NodeType)
                : throw new NotSupportedException("Invalid equality/comparison");

    private BsonDocument GenerateEqualityComparison(VectorStoreRecordPropertyModel property, object? value, ExpressionType nodeType)
    {
        if (value is null)
        {
            throw new NotSupportedException("MongogDB does not support null checks in vector search pre-filters");
        }

        // Short form of equality (instead of $eq)
        if (nodeType is ExpressionType.Equal)
        {
            return new BsonDocument { [property.StorageName] = BsonValue.Create(value) };
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

        return new BsonDocument { [property.StorageName] = new BsonDocument { [filterOperator] = BsonValue.Create(value) } };
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
                    ["$in"] = new BsonArray(from object? element in elements select BsonValue.Create(element))
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
}
