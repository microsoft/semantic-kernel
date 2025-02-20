// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.SemanticKernel.Connectors;

internal partial class SqlFilterTranslator
{
    private readonly Dictionary<string, object> _parameters = new();

    internal Dictionary<string, object> Parameters => this._parameters;

    private void GenerateLiteral(bool value)
        => this._sql.Append(value ? "TRUE" : "FALSE");

    private void GenerateLiteral(DateTime dateTime)
        => throw new NotImplementedException();

    private void GenerateLiteral(DateTimeOffset dateTimeOffset)
        => throw new NotImplementedException();

    // TODO: support Contains over array fields (#10343)
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

    private void TranslateLambdaVariables(string name, object? value)
    {
        // For null values, simply inline rather than parameterize; parameterized NULLs require setting NpgsqlDbType which is a bit more complicated,
        // plus in any case equality with NULL requires different SQL (x IS NULL rather than x = y)
        if (value is null)
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

            this._parameters.Add(name, value);
            this._sql.Append('@').Append(name);
        }
    }
}
