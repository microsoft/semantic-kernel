// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.ConnectorSupport.Filter;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchFilterTranslator
{
    private VectorStoreRecordModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    private readonly StringBuilder _filter = new();

    private static readonly char[] s_searchInDefaultDelimiter = [' ', ','];

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
            case BinaryExpression binary:
                this.TranslateBinary(binary);
                return;

            case ConstantExpression constant:
                this.TranslateConstant(constant);
                return;

            case MemberExpression member:
                this.TranslateMember(member);
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
        this._filter.Append('(');
        this.Translate(binary.Left);

        this._filter.Append(binary.NodeType switch
        {
            ExpressionType.Equal => " eq ",
            ExpressionType.NotEqual => " ne ",

            ExpressionType.GreaterThan => " gt ",
            ExpressionType.GreaterThanOrEqual => " ge ",
            ExpressionType.LessThan => " lt ",
            ExpressionType.LessThanOrEqual => " le ",

            ExpressionType.AndAlso => " and ",
            ExpressionType.OrElse => " or ",

            _ => throw new NotSupportedException("Unsupported binary expression node type: " + binary.NodeType)
        });

        this.Translate(binary.Right);
        this._filter.Append(')');
    }

    private void TranslateConstant(ConstantExpression constant)
        => this.GenerateLiteral(constant.Value);

    private void GenerateLiteral(object? value)
    {
        // TODO: Nullable
        switch (value)
        {
            case byte b:
                this._filter.Append(b);
                return;
            case short s:
                this._filter.Append(s);
                return;
            case int i:
                this._filter.Append(i);
                return;
            case long l:
                this._filter.Append(l);
                return;

            case string s:
                this._filter.Append('\'').Append(s.Replace("'", "''")).Append('\''); // TODO: escaping
                return;
            case bool b:
                this._filter.Append(b ? "true" : "false");
                return;
            case Guid g:
                this._filter.Append('\'').Append(g.ToString()).Append('\'');
                return;

            case DateTime:
            case DateTimeOffset:
                throw new NotImplementedException();

            case Array:
                throw new NotImplementedException();

            case null:
                this._filter.Append("null");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression)
    {
        if (this.TryBindProperty(memberExpression, out var property))
        {
            this._filter.Append(property.StorageName); // TODO: Escape
            return;
        }

        throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
        switch (methodCall)
        {
            // Dictionary access for dynamic mapping (r => r["SomeString"] == "foo")
            case MethodCallExpression when this.TryBindProperty(methodCall, out var property):
                this._filter.Append(property.StorageName); // TODO: Escape
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
        switch (source)
        {
            // Contains over array field (r => r.Strings.Contains("foo"))
            case var _ when this.TryBindProperty(source, out _):
                this.Translate(source);
                this._filter.Append("/any(t: t eq ");
                this.Translate(item);
                this._filter.Append(')');
                return;

            // Contains over inline enumerable
            case NewArrayExpression newArray:
                var elements = new object?[newArray.Expressions.Count];

                for (var i = 0; i < newArray.Expressions.Count; i++)
                {
                    if (newArray.Expressions[i] is not ConstantExpression { Value: var elementValue })
                    {
                        throw new NotSupportedException("Invalid element in array");
                    }

                    if (elementValue is not string)
                    {
                        throw new NotSupportedException("Contains over non-string arrays is not supported");
                    }

                    elements[i] = elementValue;
                }

                ProcessInlineEnumerable(elements, item);
                return;

            case ConstantExpression { Value: IEnumerable enumerable and not string }:
                ProcessInlineEnumerable(enumerable, item);
                return;

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }

        void ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            this._filter.Append("search.in(");
            this.Translate(item);
            this._filter.Append(", '");

            string delimiter = ", ";
            var startingPosition = this._filter.Length;

RestartLoop:
            var isFirst = true;
            foreach (string element in elements)
            {
                if (isFirst)
                {
                    isFirst = false;
                }
                else
                {
                    this._filter.Append(delimiter);
                }

                // The default delimiter for search.in() is comma or space.
                // If any element contains a comma or space, we switch to using pipe as the delimiter.
                // If any contains a pipe, we throw (for now).
                switch (delimiter)
                {
                    case ", ":
                        if (element.IndexOfAny(s_searchInDefaultDelimiter) > -1)
                        {
                            delimiter = "|";
                            this._filter.Length = startingPosition;
                            goto RestartLoop;
                        }

                        break;

                    case "|":
                        if (element.Contains('|'))
                        {
                            throw new NotSupportedException("Some elements contain both commas/spaces and pipes, cannot translate Contains");
                        }

                        break;
                }

                this._filter.Append(element.Replace("'", "''"));
            }

            this._filter.Append('\'');

            if (delimiter != ", ")
            {
                this._filter
                    .Append(", '")
                    .Append(delimiter)
                    .Append('\'');
            }

            this._filter.Append(')');
        }
    }

    private void TranslateUnary(UnaryExpression unary)
    {
        switch (unary.NodeType)
        {
            case ExpressionType.Not:
                // Special handling for !(a == b) and !(a != b)
                if (unary.Operand is BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary)
                {
                    this.TranslateBinary(
                        Expression.MakeBinary(
                            binary.NodeType is ExpressionType.Equal ? ExpressionType.NotEqual : ExpressionType.Equal,
                            binary.Left,
                            binary.Right));
                    return;
                }

                this._filter.Append("(not ");
                this.Translate(unary.Operand);
                this._filter.Append(')');
                return;

            // Handle convert over member access, for dynamic dictionary access (r => (int)r["SomeInt"] == 8)
            case ExpressionType.Convert when this.TryBindProperty(unary.Operand, out var property) && unary.Type == property.Type:
                this._filter.Append(property.StorageName); // TODO: Escape
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
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
