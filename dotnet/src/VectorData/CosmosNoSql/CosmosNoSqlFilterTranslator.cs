// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

internal class CosmosNoSqlFilterTranslator
{
    private CollectionModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    private readonly Dictionary<string, object?> _parameters = [];
    private readonly StringBuilder _sql = new();

    internal (string WhereClause, Dictionary<string, object?> Parameters) Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        Debug.Assert(this._sql.Length == 0);

        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { SupportsParameterization = true };
        var preprocessedExpression = preprocessor.Preprocess(lambdaExpression.Body);

        this.Translate(preprocessedExpression);

        return (this._sql.ToString(), this._parameters);
    }

    private void Translate(Expression? node)
    {
        switch (node)
        {
            case BinaryExpression binary:
                this.TranslateBinary(binary);
                return;

            case ConstantExpression constant:
                this.TranslateConstant(constant);
                return;

            case QueryParameterExpression { Name: var name, Value: var value }:
                this.TranslateQueryParameter(name, value);
                return;

            case MemberExpression member:
                this.TranslateMember(member);
                return;

            case NewArrayExpression newArray:
                this.TranslateNewArray(newArray);
                return;

            case MethodCallExpression methodCall:
                this.TranslateMethodCall(methodCall);
                return;

            case UnaryExpression unary:
                this.TranslateUnary(unary);
                return;

            default:
                throw new NotSupportedException("Unsupported NodeType in filter: " + node?.NodeType);
        }
    }

    private void TranslateBinary(BinaryExpression binary)
    {
        this._sql.Append('(');
        this.Translate(binary.Left);

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

        this.Translate(binary.Right);
        this._sql.Append(')');
    }

    private void TranslateConstant(ConstantExpression constant)
        => this.TranslateConstant(constant.Value);

    private void TranslateConstant(object? value)
    {
        switch (value)
        {
            case byte v:
                this._sql.Append(v);
                return;
            case short v:
                this._sql.Append(v);
                return;
            case int v:
                this._sql.Append(v);
                return;
            case long v:
                this._sql.Append(v);
                return;

            case float v:
                this._sql.Append(v);
                return;
            case double v:
                this._sql.Append(v);
                return;

            case string v:
                this._sql.Append('"').Append(v.Replace(@"\", @"\\").Replace("\"", "\\\"")).Append('"');
                return;
            case bool v:
                this._sql.Append(v ? "true" : "false");
                return;
            case Guid v:
                this._sql.Append('"').Append(v.ToString()).Append('"');
                return;

            case DateTimeOffset v:
                // Cosmos doesn't support DateTimeOffset with non-zero offset, so we convert it to UTC.
                // See https://github.com/dotnet/efcore/issues/35310
                this._sql
                    .Append('"')
                    .Append(v.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.FFFFFF", CultureInfo.InvariantCulture))
                    .Append("Z\"");
                return;

            case IEnumerable v when v.GetType() is var type && (type.IsArray || type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>)):
                this._sql.Append('[');

                var i = 0;
                foreach (var element in v)
                {
                    if (i++ > 0)
                    {
                        this._sql.Append(',');
                    }

                    this.TranslateConstant(element);
                }

                this._sql.Append(']');
                return;

            case null:
                this._sql.Append("null");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression)
    {
        if (this.TryBindProperty(memberExpression, out var property))
        {
            this.GeneratePropertyAccess(property);
            return;
        }

        throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
    }

    private void TranslateNewArray(NewArrayExpression newArray)
    {
        this._sql.Append('[');

        for (var i = 0; i < newArray.Expressions.Count; i++)
        {
            if (i > 0)
            {
                this._sql.Append(", ");
            }

            this.Translate(newArray.Expressions[i]);
        }

        this._sql.Append(']');
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
        switch (methodCall)
        {
            // Dictionary access for dynamic mapping (r => r["SomeString"] == "foo")
            case MethodCallExpression when this.TryBindProperty(methodCall, out var property):
                this.GeneratePropertyAccess(property);
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

            default:
                throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}");
        }

        static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
        {
            if (expression is UnaryExpression
                {
                    NodeType: ExpressionType.Convert,
                    Method: { Name: "op_Implicit", DeclaringType: { IsGenericType: true } implicitCastDeclaringType },
                    Operand: var unwrapped
                }
                && implicitCastDeclaringType.GetGenericTypeDefinition() is var genericTypeDefinition
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
        this._sql.Append("ARRAY_CONTAINS(");
        this.Translate(source);
        this._sql.Append(", ");
        this.Translate(item);
        this._sql.Append(')');
    }

    private void TranslateUnary(UnaryExpression unary)
    {
        switch (unary.NodeType)
        {
            // Special handling for !(a == b) and !(a != b)
            case ExpressionType.Not:
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
                this.Translate(unary.Operand);
                this._sql.Append(')');
                return;

            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            case ExpressionType.Convert when Nullable.GetUnderlyingType(unary.Type) == unary.Operand.Type:
                this.Translate(unary.Operand);
                return;

            // Handle convert over member access, for dynamic dictionary access (r => (int)r["SomeInt"] == 8)
            case ExpressionType.Convert when this.TryBindProperty(unary.Operand, out var property) && unary.Type == property.Type:
                this.GeneratePropertyAccess(property);
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }

    protected void TranslateQueryParameter(string name, object? value)
    {
        name = '@' + name;
        this._parameters.Add(name, value);
        this._sql.Append(name);
    }

    protected virtual void GeneratePropertyAccess(PropertyModel property)
        => this._sql.Append(CosmosNoSqlConstants.ContainerAlias).Append("[\"").Append(property.StorageName).Append("\"]");

    private bool TryBindProperty(Expression expression, [NotNullWhen(true)] out PropertyModel? property)
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
