// Copyright (c) Microsoft. All rights reserved.

using System;
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
        => this._sql.Append(value ? "TRUE" : "FALSE");

    private void GenerateLiteral(DateTime dateTime)
        => throw new NotImplementedException();

    private void GenerateLiteral(DateTimeOffset dateTimeOffset)
        => throw new NotImplementedException();

    private void TranslateContainsOverArrayColumn(Expression source, Expression item)
    {
        this.Translate(source);
        this._sql.Append(" @> ARRAY[");
        this.Translate(item);
        this._sql.Append(']');
    }

    private void TranslateContainsOverCapturedArray(Expression source, Expression item, object? _)
    {
        this.Translate(item);
        this._sql.Append(" = ANY (");
        this.Translate(source);
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
            this._sql.Append('$').Append(this._parameterIndex++);
        }
    }
}
