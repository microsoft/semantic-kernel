// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal sealed class PostgresFilterTranslator : SqlFilterTranslator
{
    private readonly List<object> _parameterValues = new();
    private int _parameterIndex;

    internal PostgresFilterTranslator(
        VectorStoreRecordModel model,
        LambdaExpression lambdaExpression,
        int startParamIndex,
        StringBuilder? sql = null) : base(model, lambdaExpression, sql)
    {
        this._parameterIndex = startParamIndex;
    }

    internal List<object> ParameterValues => this._parameterValues;

    protected override void TranslateContainsOverArrayColumn(Expression source, Expression item)
    {
        this.Translate(source);
        this._sql.Append(" @> ARRAY[");
        this.Translate(item);
        this._sql.Append(']');
    }

    protected override void TranslateContainsOverParameterizedArray(Expression source, Expression item, object? value)
    {
        this.Translate(item);
        this._sql.Append(" = ANY (");
        this.Translate(source);
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
            this._sql.Append('$').Append(this._parameterIndex++);
        }
    }
}
