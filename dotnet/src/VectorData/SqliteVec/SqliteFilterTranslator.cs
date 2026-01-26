// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

internal sealed class SqliteFilterTranslator : SqlFilterTranslator
{
    private readonly Dictionary<string, object> _parameters = [];

    internal SqliteFilterTranslator(CollectionModel model, LambdaExpression lambdaExpression)
        : base(model, lambdaExpression, sql: null)
    {
    }

    internal Dictionary<string, object> Parameters => this._parameters;

    protected override void TranslateConstant(object? value, bool isSearchCondition)
    {
        switch (value)
        {
            case Guid g:
                // Microsoft.Data.Sqlite writes GUIDs as upper-case strings, align our constant formatting with that.
                this._sql.Append('\'').Append(g.ToString().ToUpperInvariant()).Append('\'');
                break;
            default:
                base.TranslateConstant(value, isSearchCondition);
                break;
        }
    }

    // TODO: support Contains over array fields (#10343)
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
            // The param name is just the index, so there is no need for escaping or quoting.
            int index = this._sql.Length;
            this._sql.Append('@').Append(this._parameters.Count + 1);
            string paramName = this._sql.ToString(index, this._sql.Length - index);
            this._parameters.Add(paramName, value);
        }
    }
}
