// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

internal sealed class SqliteWhereEqualsCondition(string operand, object value)
    : SqliteWhereCondition(operand, [value])
{
    public override string BuildQuery(List<string> parameterNames)
    {
        const string EqualsOperator = "=";

        Verify.True(parameterNames.Count > 0, $"Cannot build '{nameof(SqliteWhereEqualsCondition)}' condition without parameter name.");

        return $"{this.GetOperand()} {EqualsOperator} {parameterNames[0]}";
    }
}
