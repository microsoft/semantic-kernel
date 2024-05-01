// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI.ToolBehaviors;

public sealed class NoneFunctionCallChoice : FunctionCallChoice
{
    public override FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context)
    {
        return new FunctionCallChoiceConfiguration()
        {
            MaximumAutoInvokeAttempts = 0,
            MaximumUseAttempts = 0,
            AllowAnyRequestedKernelFunction = false
        };
    }
}
