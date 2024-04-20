// Copyright (c) Microsoft. All rights reserved.

using Prompty.Core.Parsers;
using Prompty.Core.Renderers;
namespace Microsoft.SemanticKernel.PromptTemplates.Prompty.Extensions;
public static class PromptyKernelExtension
{
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel _,
        global::Prompty.Core.Prompty prompty)
    {
        var promptFunction = new PromptyKernelFunction(prompty);

        return promptFunction;
    }
}
