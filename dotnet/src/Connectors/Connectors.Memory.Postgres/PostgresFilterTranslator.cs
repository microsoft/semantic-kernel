// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal sealed class PostgresFilterTranslator : SqlFilterTranslator
{
    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    internal PostgresFilterTranslator(
        IReadOnlyDictionary<string, string> storagePropertyNames,
        LambdaExpression lambdaExpression,
        int startParamIndex) : base(storagePropertyNames, lambdaExpression, sql: null)
    {
        this._parameterIndex = startParamIndex;
    }

    internal List<object> ParameterValues => this._parameterValues;

    protected override void TranslateContainsOverArrayColumn(Expression source, Expression item, MethodCallExpression parent)
    {
        this.Translate(source, parent);
        this._sql.Append(" @> ARRAY[");
        this.Translate(item, parent);
        this._sql.Append(']');
    }

    protected override void TranslateContainsOverCapturedArray(Expression source, Expression item, MethodCallExpression parent, object? value)
    {
        this.Translate(item, parent);
        this._sql.Append(" = ANY (");
        this.Translate(source, parent);
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
            this._sql.Append('$').Append(this._parameterIndex++);
        }
    }
}
