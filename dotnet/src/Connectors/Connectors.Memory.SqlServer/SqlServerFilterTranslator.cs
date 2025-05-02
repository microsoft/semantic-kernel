// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerFilterTranslator : SqlFilterTranslator
{
    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    internal SqlServerFilterTranslator(
        VectorStoreRecordModel model,
        LambdaExpression lambdaExpression,
        StringBuilder sql,
        int startParamIndex)
        : base(model, lambdaExpression, sql)
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

    protected override void GenerateColumn(string column, bool isSearchCondition = false)
    {
        this._sql.Append('[').Append(column).Append(']');

        // "SELECT * FROM MyTable WHERE BooleanColumn;" is not supported.
        // "SELECT * FROM MyTable WHERE BooleanColumn = 1;" is supported.
        if (isSearchCondition)
        {
            this._sql.Append(" = 1");
        }
    }

    protected override void TranslateContainsOverArrayColumn(Expression source, Expression item)
        => throw new NotSupportedException("Unsupported Contains expression");

    protected override void TranslateContainsOverParameterizedArray(Expression source, Expression item, object? value)
    {
        if (value is not IEnumerable elements)
        {
            throw new NotSupportedException("Unsupported Contains expression");
        }

        this.Translate(item);
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

    protected override void TranslateQueryParameter(string name, object? value)
    {
        // For null values, simply inline rather than parameterize; parameterized NULLs require setting NpgsqlDbType which is a bit more complicated,
        // plus in any case equality with NULL requires different SQL (x IS NULL rather than x = y)
        if (value is null)
        {
            this._sql.Append("NULL");
        }
        else
        {
            this._parameterValues.Add(value);
            // SQL Server parameters can't start with a digit (but underscore is OK).
            this._sql.Append("@_").Append(this._parameterIndex++);
        }
    }
}
