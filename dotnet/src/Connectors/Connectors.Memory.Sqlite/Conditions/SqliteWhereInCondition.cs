// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite.Conditions;

internal sealed record SqliteWhereInCondition(string Operand, List<object> Values, string? TableName = null)
    : SqliteWhereCondition(Operand, Values, TableName)
{
    public override string Build(List<string> parameterNames)
    {
        const string InOperator = "IN";

        Verify.True(parameterNames.Count > 0, $"Cannot build '{nameof(SqliteWhereInCondition)}' condition without parameter names.");

        return $"{this.GetOperand()} {InOperator} ({string.Join(", ", parameterNames)})";
    }
}
