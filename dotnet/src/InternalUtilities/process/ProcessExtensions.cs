// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class ProcessExtensions
{
    public static KernelProcess CloneProcess(this KernelProcess process, ILogger logger)
    {
        string? newId = !string.IsNullOrWhiteSpace(process.State.Id) ? Guid.NewGuid().ToString("n") : null;
        KernelProcess copy =
            new(
                new KernelProcessState(process.State.Name, newId),
                process.Steps.Select(s => s.Clone(logger)).ToArray(),
                process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }
}
