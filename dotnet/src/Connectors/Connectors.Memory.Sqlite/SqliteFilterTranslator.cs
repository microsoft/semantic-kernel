// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal sealed class SqliteFilterTranslator : SqlFilterTranslator
{
    private readonly Dictionary<string, object> _parameters = new();

    internal SqliteFilterTranslator(IReadOnlyDictionary<string, string> storagePropertyNames,
        LambdaExpression lambdaExpression) : base(storagePropertyNames, lambdaExpression, sql: null)
    {
    }

    internal Dictionary<string, object> Parameters => this._parameters;

    // TODO: support Contains over array fields (#10343)
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
            // Duplicate parameter name, create a new parameter with a different name
            // TODO: Share the same parameter when it references the same captured value
            if (this._parameters.ContainsKey(name))
            {
                var baseName = name;
                var i = 0;
                do
                {
                    name = baseName + (i++);
                } while (this._parameters.ContainsKey(name));
            }

            this._parameters.Add(name, capturedValue);
            this._sql.Append('@').Append(name);
        }
    }
}
