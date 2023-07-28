// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel;

public static class KernelExtensions
{
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        string skillName,
        string functionName,
        string? input = null,
        IEnumerable<KeyValuePair<string, string>>? args = null,
        CancellationToken cancellationToken = default)
    {
        var function = kernel.Func(skillName, functionName);
        if (function == null)
        {
            throw new ArgumentException($"Function {functionName} not found in skill {skillName}");
        }

        return kernel.RunAsync(function, input, args, cancellationToken);
    }
}
