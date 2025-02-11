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
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchFilterTranslator
{
    private IReadOnlyDictionary<string, string> _storagePropertyNames = null!;
    private ParameterExpression _recordParameter = null!;

    private readonly StringBuilder _filter = new();

    private static readonly char[] s_searchInDefaultDelimiter = [' ', ','];

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
        switch (memberExpression)
        {
            case var _ when this.TryGetField(memberExpression, out var column):
                this._filter.Append(column); // TODO: Escape
                return;

            // Identify captured lambda variables, inline them as constants
            case var _ when TryGetCapturedValue(memberExpression, out var capturedValue):
                this.GenerateLiteral(capturedValue);
                return;

            default:
                throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
        }
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
        switch (source)
        {
            // Contains over array field (r => r.Strings.Contains("foo"))
            case var _ when this.TryGetField(source, out _):
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
                    if (!TryGetConstant(newArray.Expressions[i], out var elementValue))
                    {
                        throw new NotSupportedException("Invalid element in array");
                    }

                    elements[i] = elementValue;
                }

                ProcessInlineEnumerable(elements, item);
                return;

            // Contains over captured enumerable (we inline)
            case var _ when TryGetConstant(source, out var constantEnumerable)
                            && constantEnumerable is IEnumerable enumerable and not string:
                ProcessInlineEnumerable(enumerable, item);
                return;

            default:
                throw new NotSupportedException("Unsupported Contains expression");
        }

        void ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            if (item.Type != typeof(string))
            {
                throw new NotSupportedException("Contains over non-string arrays is not supported");
            }

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

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }

    private bool TryGetField(Expression expression, [NotNullWhen(true)] out string? field)
    {
        if (expression is MemberExpression member && member.Expression == this._recordParameter)
        {
            if (!this._storagePropertyNames.TryGetValue(member.Member.Name, out field))
            {
                throw new InvalidOperationException($"Property name '{member.Member.Name}' provided as part of the filter clause is not a valid property name.");
            }

            return true;
        }

        field = null;
        return false;
    }

    private static bool TryGetCapturedValue(Expression expression, out object? capturedValue)
    {
        if (expression is MemberExpression { Expression: ConstantExpression constant, Member: FieldInfo fieldInfo }
            && constant.Type.Attributes.HasFlag(TypeAttributes.NestedPrivate)
            && Attribute.IsDefined(constant.Type, typeof(CompilerGeneratedAttribute), inherit: true))
        {
            capturedValue = fieldInfo.GetValue(constant.Value);
            return true;
        }

        capturedValue = null;
        return false;
    }

    private static bool TryGetConstant(Expression expression, out object? constantValue)
    {
        switch (expression)
        {
            case ConstantExpression { Value: var v }:
                constantValue = v;
                return true;

            case var _ when TryGetCapturedValue(expression, out var capturedValue):
                constantValue = capturedValue;
                return true;

            default:
                constantValue = null;
                return false;
        }
    }
}
