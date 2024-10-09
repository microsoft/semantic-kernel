// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal sealed record SqliteWhereMatchCondition(string Operand, object Value, string? TableName = null)
    : SqliteWhereCondition(Operand, [Value], TableName)
{
    public override string Build(List<string> parameterNames)
    {
        const string MatchOperator = "MATCH";

        Verify.True(parameterNames.Count > 0, $"Cannot build '{nameof(SqliteWhereMatchCondition)}' condition without parameter name.");

        return $"{this.GetOperand()} {MatchOperator} {parameterNames[0]}";
    }
}
