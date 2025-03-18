// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerFilterTranslator : SqlFilterTranslator
{
    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    internal SqlServerFilterTranslator(
        IReadOnlyDictionary<string, string> storagePropertyNames,
        LambdaExpression lambdaExpression,
        StringBuilder sql,
        int startParamIndex)
        : base(storagePropertyNames, lambdaExpression, sql)
    {
        this._parameterIndex = startParamIndex;
    }

    internal List<object> ParameterValues => this._parameterValues;

    protected override void TranslateConstant(object? value)
    {
        switch (value)
        {
            case bool boolValue:
                this._sql.Append(boolValue ? "1" : "0");
                return;
            case DateTime dateTime:
                this._sql.AppendFormat("'{0:yyyy-MM-dd HH:mm:ss}'", dateTime);
                return;
            case DateTimeOffset dateTimeOffset:
                this._sql.AppendFormat("'{0:yyy-MM-dd HH:mm:ss zzz}'", dateTimeOffset);
                return;
            default:
                base.TranslateConstant(value);
                break;
        }
    }

    protected override void TranslateColumn(string column, MemberExpression memberExpression, Expression? parent)
    {
        // "SELECT * FROM MyTable WHERE BooleanColumn;" is not supported.
        // "SELECT * FROM MyTable WHERE BooleanColumn = 1;" is supported.
        if (memberExpression.Type == typeof(bool)
            && (parent is null // Where(x => x.Bool)
                || parent is UnaryExpression { NodeType: ExpressionType.Not } // Where(x => !x.Bool)
                || parent is BinaryExpression { NodeType: ExpressionType.AndAlso or ExpressionType.OrElse })) // Where(x => x.Bool && other)
        {
            this.TranslateBinary(Expression.Equal(memberExpression, Expression.Constant(true)));
        }
        else
        {
            this._sql.Append('[').Append(column).Append(']');
        }
    }

    protected override void TranslateContainsOverArrayColumn(Expression source, Expression item, MethodCallExpression parent)
        => throw new NotSupportedException("Unsupported Contains expression");

    protected override void TranslateContainsOverCapturedArray(Expression source, Expression item, MethodCallExpression parent, object? value)
    {
        if (value is not IEnumerable elements)
        {
            throw new NotSupportedException("Unsupported Contains expression");
        }

        this.Translate(item, parent);
        this._sql.Append(" IN (");

        var isFirst = true;
        foreach (var element in elements)
        {
            if (isFirst)
            {
                isFirst = false;
            }
            else
            {
                this._sql.Append(", ");
            }

            this.TranslateConstant(element);
        }

        this._sql.Append(')');
    }

    protected override void TranslateCapturedVariable(string name, object? capturedValue)
    {
        // For null values, simply inline rather than parameterize; parameterized NULLs require setting NpgsqlDbType which is a bit more complicated,
        // plus in any case equality with NULL requires different SQL (x IS NULL rather than x = y)
        if (capturedValue is null)
        {
            this._sql.Append("NULL");
        }
        else
        {
            this._parameterValues.Add(capturedValue);
            // SQL Server parameters can't start with a digit (but underscore is OK).
            this._sql.Append("@_").Append(this._parameterIndex++);
        }
    }
}
