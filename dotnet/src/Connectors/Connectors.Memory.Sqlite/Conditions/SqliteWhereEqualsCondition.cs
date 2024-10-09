// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite.Conditions;

internal sealed record SqliteWhereEqualsCondition(string Operand, object Value, string? TableName = null)
    : SqliteWhereCondition(Operand, [Value], TableName)
{
    public override string Build(List<string> parameterNames)
    {
        const string EqualsOperator = "=";

        Verify.True(parameterNames.Count > 0, $"Cannot build '{nameof(SqliteWhereEqualsCondition)}' condition without parameter name.");

        return $"{this.GetOperand()} {EqualsOperator} {parameterNames[0]}";
    }
}
