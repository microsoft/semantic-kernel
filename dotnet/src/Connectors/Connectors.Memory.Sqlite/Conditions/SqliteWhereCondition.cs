// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal abstract class SqliteWhereCondition(string operand, List<object> values)
{
    public string Operand { get; set; } = operand;

    public List<object> Values { get; set; } = values;

    public string? TableName { get; set; }

    public abstract string BuildQuery(List<string> parameterNames);

    protected string GetOperand() => !string.IsNullOrWhiteSpace(this.TableName) ?
        $"\"{this.TableName}\".\"{this.Operand}\"" :
        $"\"{this.Operand}\"";
}
