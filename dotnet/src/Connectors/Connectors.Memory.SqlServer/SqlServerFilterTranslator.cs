// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.SemanticKernel.Connectors;

internal partial class SqlFilterTranslator
{
    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    internal List<object> ParameterValues => this._parameterValues;

    internal void Initialize(int startParamIndex)
    {
        this._parameterIndex = startParamIndex;
    }

    private void GenerateLiteral(bool value)
        => this._sql.Append(value ? "1" : "0");

    private void GenerateLiteral(DateTime dateTime)
        => this._sql.AppendFormat("'{0:yyyy-MM-dd HH:mm:ss}'", dateTime);

    private void GenerateLiteral(DateTimeOffset dateTimeOffset)
        => this._sql.AppendFormat("'{0:yyy-MM-dd HH:mm:ss zzz}'", dateTimeOffset);

    private void TranslateContainsOverArrayColumn(Expression source, Expression item)
        => throw new NotSupportedException("Unsupported Contains expression");

    private void TranslateContainsOverCapturedArray(Expression source, Expression item, object? value)
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

            this.GenerateLiteral(element);
        }

        this._sql.Append(')');
    }

    private void TranslateLambdaVariables(string _, object? capturedValue)
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
            // SQL Server paramters can't start with a digit (but underscore is OK).
            this._sql.Append("@_").Append(this._parameterIndex++);
        }
    }
}
