// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Planners.Stepwise;
internal class FunctionCallingStepwisePlannerResult
{
    public string Message { get; } = string.Empty;

    public ChatHistory History { get; }

    public FunctionCallingStepwisePlannerResult(string message, ChatHistory history)
    {
        this.Message = message;
        this.History = history;
    }
}
