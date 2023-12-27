// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public class FunctionInvokingContext : FunctionFilterContext
{
    public FunctionInvokingContext(KernelFunction function, KernelArguments arguments)
        : base(function, arguments, metadata: null)
    {
    }
}
