// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;
public sealed class ToolInvokingContext : ToolFilterContext
{
    public ToolInvokingContext(ToolCallBehavior toolCallBehavior, int modelIteration, KernelFunction function, KernelArguments? arguments, ChatHistory chatHistory)
    : base(toolCallBehavior, modelIteration, function, arguments, metadata: null, chatHistory)
    {
    }
}
