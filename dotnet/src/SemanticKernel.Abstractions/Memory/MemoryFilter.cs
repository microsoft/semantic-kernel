// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory;

public enum MemoryFieldOperator
{
    Equals,
    GreaterThan,
    LowerThan,
    GreaterThanOrEqual,
    LowerThanOrEqual,
    Contains
}

public class MemoryFilter
{
    public string Field { get; set; }
    public MemoryFieldOperator Operator { get; set; }
    public object Value { get; set; }

    public MemoryFilter(string field, MemoryFieldOperator op, object value)
    {
        this.Field = field;
        this.Operator = op;
        this.Value = value;
    }
}
