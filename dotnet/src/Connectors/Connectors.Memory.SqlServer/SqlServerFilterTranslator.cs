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

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal class SqlServerFilterTranslator(StringBuilder sql, string schema)
{
    private IReadOnlyDictionary<string, string> _storagePropertyNames = null!;
    private ParameterExpression _recordParameter = null!;

    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    private readonly StringBuilder _sql = sql;
    private readonly string _schema = schema;

    internal List<object> Translate(
        IReadOnlyDictionary<string, string> storagePropertyNames,
        LambdaExpression lambdaExpression,
        int startParamIndex)
    {
        this._storagePropertyNames = storagePropertyNames;
        this._parameterIndex = startParamIndex;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        this._sql.Append("WHERE ");
        this.Translate(lambdaExpression.Body);
        return this._parameterValues;
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
        // Special handling for null comparisons
        switch (binary.NodeType)
        {
            case ExpressionType.Equal when IsNull(binary.Right):
                this._sql.Append('(');
                this.Translate(binary.Left);
                this._sql.Append(" IS NULL)");
                return;
            case ExpressionType.NotEqual when IsNull(binary.Right):
                this._sql.Append('(');
                this.Translate(binary.Left);
                this._sql.Append(" IS NOT NULL)");
                return;

            case ExpressionType.Equal when IsNull(binary.Left):
                this._sql.Append('(');
                this.Translate(binary.Right);
                this._sql.Append(" IS NULL)");
                return;
            case ExpressionType.NotEqual when IsNull(binary.Left):
                this._sql.Append('(');
                this.Translate(binary.Right);
                this._sql.Append(" IS NOT NULL)");
                return;
        }

        this._sql.Append('(');
        this.Translate(binary.Left);

        // SQL Server uses the same values as PostgreSQL.
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

        static bool IsNull(Expression expression)
            => expression is ConstantExpression { Value: null }
               || (TryGetCapturedValue(expression, out var capturedValue) && capturedValue is null);
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
                this._sql.Append('\'').Append(s.Replace("'", "''")).Append('\'');
                return;
            case bool b:
                // SQL Server uses 1 and 0 to represent booleans.
                this._sql.Append(b ? "1" : "0");
                return;
            case Guid g:
                this._sql.Append('\'').Append(g.ToString()).Append('\'');
                return;

            case DateTime dateTime:
                // SQL Server supports DateTimes in this particular format
                this._sql.AppendFormat("'{0:yyyy-MM-dd HH:mm:ss}'", dateTime);
                return;

            case DateTimeOffset dateTimeOffset:
                // SQL Server supports DateTimeOffsets in this particular format
                this._sql.AppendFormat("'{0:yyy-MM-dd HH:mm:ss zzz}'", dateTimeOffset);
                return;

            case Array:
                throw new NotImplementedException();

            case null:
                this._sql.Append("NULL");
                return;

            default:
                throw new NotSupportedException("Unsupported constant type: " + constant.Value.GetType().Name);
        }
    }

    private void TranslateMember(MemberExpression memberExpression)
    {
        switch (memberExpression)
        {
            case var _ when this.TryGetColumn(memberExpression, out var column):
                // SQL Server uses square brackets to escape column names and requires the schema to be provided.
                //this._sql.AppendTableName(this._schema, column);
                this._sql.Append('"').Append(column).Append('"');
                return;

            // Identify captured lambda variables, translate to PostgreSQL parameters ($1, $2...)
            case var _ when TryGetCapturedValue(memberExpression, out var capturedValue):
                // For null values, simply inline rather than parameterize; parameterized NULLs require setting NpgsqlDbType which is a bit more complicated,
                // plus in any case equality with NULL requires different SQL (x IS NULL rather than x = y)
                if (capturedValue is null)
                {
                    this._sql.Append("NULL");
                }
                else
                {
                    this._parameterValues.Add(capturedValue);
                    // SQL Server paramters can't start with a digit.
                    this._sql.Append("@_").Append(this._parameterIndex++);
                }
                return;

            default:
                throw new NotSupportedException($"Member access for '{memberExpression.Member.Name}' is unsupported - only member access over the filter parameter are supported");
        }
    }

    private void TranslateMethodCall(MethodCallExpression methodCall)
    {
        throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}");
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

                this._sql.Append("(NOT ");
                this.Translate(unary.Operand);
                this._sql.Append(')');
                return;

            default:
                throw new NotSupportedException("Unsupported unary expression node type: " + unary.NodeType);
        }
    }

    private bool TryGetColumn(Expression expression, [NotNullWhen(true)] out string? column)
    {
        if (expression is MemberExpression member && member.Expression == this._recordParameter)
        {
            if (!this._storagePropertyNames.TryGetValue(member.Member.Name, out column))
            {
                throw new InvalidOperationException($"Property name '{member.Member.Name}' provided as part of the filter clause is not a valid property name.");
            }

            return true;
        }

        column = null;
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
}
