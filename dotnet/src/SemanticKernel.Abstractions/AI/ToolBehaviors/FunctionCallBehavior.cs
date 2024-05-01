// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.ToolBehaviors;

public class FunctionCallBehavior : ToolBehavior
{
    public static FunctionCallBehavior AutoFunctionChoice(IEnumerable<KernelFunction>? enabledFunctions = null, bool autoInvoke = true)
    {
        return new FunctionCallBehavior
        {
            Choice = new AutoFunctionCallChoice(enabledFunctions ?? [])
            {
                MaximumAutoInvokeAttempts = autoInvoke ? AutoFunctionCallChoice.DefaultMaximumAutoInvokeAttempts : 0
            }
        };
    }

    public static FunctionCallBehavior RequiredFunctionChoice(IEnumerable<KernelFunction> functions, bool autoInvoke = true)
    {
        return new FunctionCallBehavior
        {
            Choice = new RequiredFunctionCallChoice(functions)
            {
                MaximumAutoInvokeAttempts = autoInvoke ? AutoFunctionCallChoice.DefaultMaximumAutoInvokeAttempts : 0
            }
        };
    }

    public static FunctionCallBehavior None { get; } = new FunctionCallBehavior() { Choice = new NoneFunctionCallChoice() };

    [JsonPropertyName("choice")]
    public FunctionCallChoice Choice { get; init; } = new NoneFunctionCallChoice();
}
