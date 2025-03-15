// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

// MongoDB query reference: https://www.mongodb.com/docs/manual/reference/operator/query
// Information specific to vector search pre-filter: https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#atlas-vector-search-pre-filter
internal class AzureCosmosDBMongoDBFilterTranslator
{
    private IReadOnlyDictionary<string, string> _storagePropertyNames = null!;
    private ParameterExpression _recordParameter = null!;

    internal BsonDocument Translate(LambdaExpression lambdaExpression, IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        this._storagePropertyNames = storagePropertyNames;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        return this.Translate(lambdaExpression.Body);
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

            // MemberExpression is generally handled within e.g. TranslateEqualityComparison; this is used to translate direct bool inside filter (e.g. Filter => r => r.Bool)
            MemberExpression member when member.Type == typeof(bool) && this.TryTranslateFieldAccess(member, out _)
                => this.TranslateEqualityComparison(Expression.Equal(member, Expression.Constant(true))),

            MethodCallExpression methodCall => this.TranslateMethodCall(methodCall),

            _ => throw new NotSupportedException("The following NodeType is unsupported: " + node?.NodeType)
        };

    private BsonDocument TranslateEqualityComparison(BinaryExpression binary)
    {
        if ((this.TryTranslateFieldAccess(binary.Left, out var storagePropertyName) && TryGetConstant(binary.Right, out var value))
            || (this.TryTranslateFieldAccess(binary.Right, out storagePropertyName) && TryGetConstant(binary.Left, out value)))
        {
            if (value is null)
            {
                throw new NotSupportedException("MongogDB does not support null checks in vector search pre-filters");
            }

            // Short form of equality (instead of $eq)
            if (binary.NodeType is ExpressionType.Equal)
            {
                return new BsonDocument { [storagePropertyName] = BsonValue.Create(value) };
            }

            var filterOperator = binary.NodeType switch
            {
                ExpressionType.NotEqual => "$ne",
                ExpressionType.GreaterThan => "$gt",
                ExpressionType.GreaterThanOrEqual => "$gte",
                ExpressionType.LessThan => "$lt",
                ExpressionType.LessThanOrEqual => "$lte",

                _ => throw new UnreachableException()
            };

            return new BsonDocument { [storagePropertyName] = new BsonDocument { [filterOperator] = BsonValue.Create(value) } };
        }

        throw new NotSupportedException("Invalid equality/comparison");
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

            // Not over bool field (Filter => r => !r.Bool)
            case MemberExpression member when member.Type == typeof(bool) && this.TryTranslateFieldAccess(member, out _):
                return this.TranslateEqualityComparison(Expression.Equal(member, Expression.Constant(false)));
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
            case var _ when this.TryTranslateFieldAccess(source, out _):
                throw new NotSupportedException("MongoDB does not support Contains within array fields ($elemMatch) in vector search pre-filters");

            // Contains over inline enumerable
            case NewArrayExpression newArray:
                var elements = new object?[newArray.Expressions.Count];

                for (var i = 0; i < newArray.Expressions.Count; i++)
                {
                    if (!TryGetConstant(newArray.Expressions[i], out var elementValue))
                    {
                        throw new NotSupportedException("Invalid element in array");
                    }

                    elements[i] = elementValue;
                }

                return ProcessInlineEnumerable(elements, item);

            // Contains over captured enumerable (we inline)
            case var _ when TryGetConstant(source, out var constantEnumerable)
                            && constantEnumerable is IEnumerable enumerable and not string:
                return ProcessInlineEnumerable(enumerable, item);

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }

        BsonDocument ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            if (!this.TryTranslateFieldAccess(item, out var storagePropertyName))
            {
                throw new NotSupportedException("Unsupported item type in Contains");
            }

            return new BsonDocument
            {
                [storagePropertyName] = new BsonDocument
                {
                    ["$in"] = new BsonArray(from object? element in elements select BsonValue.Create(element))
                }
            };
        }
    }

    private bool TryTranslateFieldAccess(Expression expression, [NotNullWhen(true)] out string? storagePropertyName)
    {
        if (expression is MemberExpression memberExpression && memberExpression.Expression == this._recordParameter)
        {
            if (!this._storagePropertyNames.TryGetValue(memberExpression.Member.Name, out storagePropertyName))
            {
                throw new InvalidOperationException($"Property name '{memberExpression.Member.Name}' provided as part of the filter clause is not a valid property name.");
            }

            return true;
        }

        storagePropertyName = null;
        return false;
    }

    private static bool TryGetConstant(Expression expression, out object? constantValue)
    {
        switch (expression)
        {
            case ConstantExpression { Value: var v }:
                constantValue = v;
                return true;

            // This identifies compiler-generated closure types which contain captured variables.
            case MemberExpression { Expression: ConstantExpression constant, Member: FieldInfo fieldInfo }
                when constant.Type.Attributes.HasFlag(TypeAttributes.NestedPrivate)
                     && Attribute.IsDefined(constant.Type, typeof(CompilerGeneratedAttribute), inherit: true):
                constantValue = fieldInfo.GetValue(constant.Value);
                return true;

            default:
                constantValue = null;
                return false;
        }
    }
}
