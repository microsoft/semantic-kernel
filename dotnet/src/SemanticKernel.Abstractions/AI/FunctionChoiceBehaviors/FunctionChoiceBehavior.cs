// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

public abstract class FunctionChoiceBehavior
{
    protected const string FunctionNameSeparator = ".";

    public static FunctionChoiceBehavior AutoFunctionChoice(IEnumerable<KernelFunction>? enabledFunctions = null, bool autoInvoke = true)
    {
        return new AutoFunctionChoiceBehavior(enabledFunctions ?? [])
        {
            MaximumAutoInvokeAttempts = autoInvoke ? AutoFunctionChoiceBehavior.DefaultMaximumAutoInvokeAttempts : 0
        };
    }

    public static FunctionChoiceBehavior RequiredFunctionChoice(IEnumerable<KernelFunction> functions, bool autoInvoke = true)
    {
        return new RequiredFunctionChoiceBehavior(functions)
        {
            MaximumAutoInvokeAttempts = autoInvoke ? AutoFunctionChoiceBehavior.DefaultMaximumAutoInvokeAttempts : 0
        };
    }

    public static FunctionChoiceBehavior None { get; } = new NoneFunctionChoiceBehavior();

    public abstract FunctionChoiceBehaviorConfiguration Configure(FunctionChoiceBehaviorContext context);
}
