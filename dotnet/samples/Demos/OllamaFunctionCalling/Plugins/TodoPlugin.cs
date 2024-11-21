// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System;
using Microsoft.SemanticKernel;

namespace OllamaFunctionCalling;

public class TodoPlugin
{
    [KernelFunction, Description("Set the completed state of a todo")]
    public void SetCompleted(
    [Description("Determines the id of the todo to toggle")] Guid id,
    [Description("Determines whether to to complete or to resume the todo")] bool complete = true)
    {
        //...
    }
}
