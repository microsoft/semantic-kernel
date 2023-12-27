// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public class PromptRenderingContext : PromptFilterContext
{
    public PromptRenderingContext(KernelFunction function, KernelArguments arguments)
        : base(function, arguments, metadata: null)
    {
    }
}
