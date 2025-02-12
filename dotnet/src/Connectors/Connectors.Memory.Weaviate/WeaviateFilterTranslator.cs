// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// https://weaviate.io/developers/weaviate/api/graphql/filters#filter-structure
internal class WeaviateFilterTranslator
{
    private IReadOnlyDictionary<string, string> _storagePropertyNames = null!;
    private ParameterExpression _recordParameter = null!;
    private readonly StringBuilder _filter = new();

    internal string Translate(LambdaExpression lambdaExpression, IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        Debug.Assert(this._filter.Length == 0);

        this._storagePropertyNames = storagePropertyNames;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        this.Translate(lambdaExpression.Body);
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
                    // Special handling for !(a == b) and !(a != b)
                    case BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary:
                        this.TranslateEqualityComparison(
                            Expression.MakeBinary(
                                binary.NodeType is ExpressionType.Equal ? ExpressionType.NotEqual : ExpressionType.Equal,
                                binary.Left,
                                binary.Right));
                        return;

                    // Not over bool field (Filter => r => !r.Bool)
                    case MemberExpression member when member.Type == typeof(bool) && this.TryTranslateFieldAccess(member, out _):
                        this.TranslateEqualityComparison(Expression.Equal(member, Expression.Constant(false)));
                        return;

                    default:
                        throw new NotSupportedException("Weaviate does not support the NOT operator (see https://github.com/weaviate/weaviate/issues/3683)");
                }
            }

            // MemberExpression is generally handled within e.g. TranslateEqual; this is used to translate direct bool inside filter (e.g. Filter => r => r.Bool)
            case MemberExpression member when member.Type == typeof(bool) && this.TryTranslateFieldAccess(member, out _):
                this.TranslateEqualityComparison(Expression.Equal(member, Expression.Constant(true)));
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
        if ((this.TryTranslateFieldAccess(binary.Left, out var storagePropertyName) && TryGetConstant(binary.Right, out var value))
            || (this.TryTranslateFieldAccess(binary.Right, out storagePropertyName) && TryGetConstant(binary.Left, out value)))
        {
            // { path: ["intPropName"], operator: Equal, ValueInt: 8 }
            this._filter
                .Append("{ path: [\"")
                .Append(JsonEncodedText.Encode(storagePropertyName))
                .Append("\"], operator: ");

            // Special handling for null comparisons
            if (value is null)
            {
                if (binary.NodeType is ExpressionType.Equal or ExpressionType.NotEqual)
                {
                    this._filter
                        .Append("IsNull, valueBoolean: ")
                        .Append(binary.NodeType is ExpressionType.Equal ? "true" : "false")
                        .Append(" }");
                    return;
                }

                throw new NotSupportedException("null value supported only with equality/inequality checks");
            }

            // Operator
            this._filter.Append(binary.NodeType switch
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

            return;
        }

        throw new NotSupportedException("Invalid equality/comparison");
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
        if (this.TryTranslateFieldAccess(source, out var storagePropertyName)
            && TryGetConstant(item, out var itemConstant)
            && itemConstant is string stringConstant)
        {
            this._filter
                .Append("{ path: [\"")
                .Append(JsonEncodedText.Encode(storagePropertyName))
                .Append("\"], operator: ContainsAny, valueText: [")
                .Append(JsonEncodedText.Encode(stringConstant))
                .Append("]}");
            return;
        }

        throw new NotSupportedException("Contains supported only over tag field");
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
