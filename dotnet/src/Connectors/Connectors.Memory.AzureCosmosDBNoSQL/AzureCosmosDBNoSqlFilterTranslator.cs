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
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.ConnectorSupport.Filter;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

internal class AzureCosmosDBNoSqlFilterTranslator
{
    private VectorStoreRecordModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    private readonly Dictionary<string, object?> _parameters = new();
    private readonly StringBuilder _sql = new();

    internal (string WhereClause, Dictionary<string, object?> Parameters) Translate(LambdaExpression lambdaExpression, VectorStoreRecordModel model)
    {
        Debug.Assert(this._sql.Length == 0);

        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { InlineCapturedVariables = false };
        var preprocessedExpression = preprocessor.Visit(lambdaExpression);

        this.Translate(lambdaExpression.Body);

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
    {
        // TODO: Nullable
        switch (constant.Value)
        {
            case byte b:
                this._sql.Append(b);
                return;
            case short s:
                this._sql.Append(s);
                return;
            case int i:
                this._sql.Append(i);
                return;
            case long l:
                this._sql.Append(l);
                return;

            case string s:
                this._sql.Append('"').Append(s.Replace(@"\", @"\\").Replace("\"", "\\\"")).Append('"');
                return;
            case bool b:
                this._sql.Append(b ? "true" : "false");
                return;
            case Guid g:
                this._sql.Append('"').Append(g.ToString()).Append('"');
                return;

            case DateTime:
            case DateTimeOffset:
                throw new NotImplementedException();

            case Array:
                throw new NotImplementedException();

            case null:
                this._sql.Append("null");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + constant.Value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression)
    {
        switch (memberExpression)
        {
            case var _ when this.TryBindProperty(memberExpression, out var property):
                this.GeneratePropertyAccess(property);
                return;

            // Identify captured lambda variables, translate to Cosmos parameters (@foo, @bar...)
            case var _ when TryGetCapturedValue(memberExpression, out var name, out var value):
                // Duplicate parameter name, create a new parameter with a different name
                // TODO: Share the same parameter when it references the same captured value
                if (this._parameters.ContainsKey(name))
                {
                    var baseName = name;
                    var i = 0;
                    do
                    {
                        name = baseName + (i++);
                    } while (this._parameters.ContainsKey(name));
                }

                name = '@' + name;
                this._parameters.Add(name, value);
                this._sql.Append(name);
                return;

            default:
                throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
        }
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

            default:
                throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}");
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

            // Handle convert over member access, for dynamic dictionary access (r => (int)r["SomeInt"] == 8)
            case ExpressionType.Convert when this.TryBindProperty(unary.Operand, out var property) && unary.Type == property.Type:
                this.GeneratePropertyAccess(property);
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }

    protected virtual void GeneratePropertyAccess(VectorStoreRecordPropertyModel property)
        => this._sql.Append(AzureCosmosDBNoSQLConstants.ContainerAlias).Append("[\"").Append(property.StorageName).Append("\"]");

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

    private static bool TryGetCapturedValue(Expression expression, [NotNullWhen(true)] out string? name, out object? value)
    {
        if (expression is MemberExpression { Expression: ConstantExpression constant, Member: FieldInfo fieldInfo }
            && constant.Type.Attributes.HasFlag(TypeAttributes.NestedPrivate)
            && Attribute.IsDefined(constant.Type, typeof(CompilerGeneratedAttribute), inherit: true))
        {
            name = fieldInfo.Name;
            value = fieldInfo.GetValue(constant.Value);
            return true;
        }

        name = null;
        value = null;
        return false;
    }
}
