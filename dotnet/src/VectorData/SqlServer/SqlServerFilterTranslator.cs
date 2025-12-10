// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
#if NET
using System.Globalization;
#endif
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerFilterTranslator : SqlFilterTranslator
{
    private readonly List<object> _parameterValues = [];
    private int _parameterIndex;

    internal SqlServerFilterTranslator(
        CollectionModel model,
        LambdaExpression lambdaExpression,
        StringBuilder sql,
        int startParamIndex)
        : base(model, lambdaExpression, sql)
    {
        this._parameterIndex = startParamIndex;
    }

    internal List<object> ParameterValues => this._parameterValues;

    protected override void TranslateConstant(object? value, bool isSearchCondition)
    {
        switch (value)
        {
            case bool boolValue when isSearchCondition:
                this._sql.Append(boolValue ? "1 = 1" : "1 = 0");
                return;
            case bool boolValue:
                this._sql.Append(boolValue ? "CAST(1 AS BIT)" : "CAST(0 AS BIT)");
                return;
            case DateTime dateTime:
                this._sql.Append('\'').Append(dateTime.ToString("o")).Append('\'');
                return;
            case DateTimeOffset dateTimeOffset:
                this._sql.Append('\'').Append(dateTimeOffset.ToString("o")).Append('\'');
                return;
#if NET
            case DateOnly dateOnly:
                this._sql.Append('\'').Append(dateOnly.ToString("o")).Append('\'');
                return;
            case TimeOnly timeOnly:
                this._sql.AppendFormat(timeOnly.Ticks % 10000000 == 0
                    ? string.Format(CultureInfo.InvariantCulture, @"'{0:HH\:mm\:ss}'", value)
                    : string.Format(CultureInfo.InvariantCulture, @"'{0:HH\:mm\:ss\.FFFFFFF}'", value));
                return;
#endif

            default:
                base.TranslateConstant(value, isSearchCondition);
                break;
        }
    }

    protected override void GenerateColumn(PropertyModel property, bool isSearchCondition = false)
    {
        // StorageName is considered to be a safe input, we quote and escape it mostly to produce valid SQL.
        this._sql.Append('[').Append(property.StorageName.Replace("]", "]]")).Append(']');

        // "SELECT * FROM MyTable WHERE BooleanColumn;" is not supported.
        // "SELECT * FROM MyTable WHERE BooleanColumn = 1;" is supported.
        if (isSearchCondition)
        {
            this._sql.Append(" = 1");
        }
    }

    protected override void TranslateContainsOverArrayColumn(Expression source, Expression item)
    {
        if (item.Type != typeof(string))
        {
            throw new NotSupportedException("Unsupported Contains expression");
        }

        this._sql.Append("JSON_CONTAINS(");
        this.Translate(source);
        this._sql.Append(", ");
        this.Translate(item);
        this._sql.Append(") = 1");
    }

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

            this.TranslateConstant(element, isSearchCondition: false);
        }

        this._sql.Append(')');
    }

    protected override void TranslateQueryParameter(object? value)
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
            // The param name is just the index, so there is no need for escaping or quoting.
            // SQL Server parameters can't start with a digit (but underscore is OK).
            this._sql.Append("@_").Append(this._parameterIndex++);
        }
    }
}
