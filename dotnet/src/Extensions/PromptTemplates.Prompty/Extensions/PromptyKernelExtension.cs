// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
namespace Microsoft.SemanticKernel.PromptTemplates.Prompty.Extensions;
public static class PromptyKernelExtension
{
    public static Task<KernelFunction> CreateFunctionFromPrompty(
        this Kernel kernel,
        global::Prompty.Core.Prompty prompty)
    {
        var modelConfig = prompty.Model;
        kernel.CreateFunctionFromPrompt
    }
}
