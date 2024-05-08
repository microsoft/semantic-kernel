// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    public override FunctionChoiceBehaviorConfiguration Configure(FunctionChoiceBehaviorContext context)
    {
        return new FunctionChoiceBehaviorConfiguration()
        {
            MaximumAutoInvokeAttempts = 0,
            MaximumUseAttempts = 0
        };
    }
}
