// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal abstract record SqliteWhereCondition(string Operand, List<object> Values, string? TableName = null)
{
    public abstract string BuildQuery(List<string> parameterNames);

    protected string GetOperand() => !string.IsNullOrWhiteSpace(this.TableName) ?
        $"{this.TableName}.{this.Operand}" :
        this.Operand;
}
