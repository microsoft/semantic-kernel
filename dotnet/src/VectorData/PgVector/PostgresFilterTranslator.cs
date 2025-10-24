// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal sealed class PostgresFilterTranslator : SqlFilterTranslator
{
    private int _parameterIndex;

    internal PostgresFilterTranslator(
        CollectionModel model,
        LambdaExpression lambdaExpression,
        int startParamIndex,
        StringBuilder? sql = null) : base(model, lambdaExpression, sql)
    {
        this._parameterIndex = startParamIndex;
    }

    internal List<object> ParameterValues { get; } = new();

    protected override void TranslateConstant(object? value, bool isSearchCondition)
    {
        switch (value)
        {
            // TODO: This aligns with our mapping of DateTime to PG's timestamp (as opposed to timestamptz) - we probably want to
            // change that to timestamptz (aligning with Npgsql and EF). See #10641.
            case DateTime dateTime:
                this._sql.Append('\'').Append(dateTime.ToString("yyyy-MM-ddTHH:mm:ss.FFFFFF", CultureInfo.InvariantCulture)).Append('\'');
                return;
            case DateTimeOffset dateTimeOffset:
                if (dateTimeOffset.Offset != TimeSpan.Zero)
                {
                    throw new NotSupportedException("DateTimeOffset with non-zero offset is not supported with PostgreSQL");
                }

                this._sql.Append('\'').Append(dateTimeOffset.ToString("yyyy-MM-ddTHH:mm:ss.FFFFFF", CultureInfo.InvariantCulture)).Append("Z'");
                return;

            // Array constants (ARRAY[1, 2, 3])
            case IEnumerable v when v.GetType() is var type && (type.IsArray || type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>)):
                this._sql.Append("ARRAY[");

                var i = 0;
                foreach (var element in v)
                {
                    if (i++ > 0)
                    {
                        this._sql.Append(',');
                    }

                    this.TranslateConstant(element, isSearchCondition: false);
                }

                this._sql.Append(']');
                return;

            default:
                base.TranslateConstant(value, isSearchCondition);
                break;
        }
    }

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
            this.ParameterValues.Add(value);
            // The param name is just the index, so there is no need for escaping or quoting.
            this._sql.Append('$').Append(this._parameterIndex++);
        }
    }
}
