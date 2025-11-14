// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class ProcessExtensions
{
    public static KernelProcess CloneProcess(this KernelProcess process, ILogger logger)
    {
        KernelProcess copy =
            new(
                new KernelProcessState(process.State.StepId, process.State.Version, process.State.RunId),
                process.Steps.Select(s => s.Clone(logger)).ToArray(),
                process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }
}
