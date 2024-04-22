// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Prompty.Extension;

public static class PromptyKernelExtension
{
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel _,
        string promptyPath)
    {
        var prompty = new Core.Prompty();
        prompty = prompty.Load(promptyPath, prompty);
        var promptFunction = new PromptyKernelFunction(prompty);

        return promptFunction;
    }
}
