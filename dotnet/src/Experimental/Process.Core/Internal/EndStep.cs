// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// EndStep is a special purpose step that is used to trigger a process to stop. It is the last step in a process.
/// </summary>
internal sealed class EndStep : ProcessStepBuilder
{
    /// <summary>
    /// The static instance of the <see cref="EndStep"/> class.
    /// </summary>
    public static EndStep Instance { get; } = new EndStep();

    /// <summary>
    /// Represents the end of a process.
    /// </summary>
    internal EndStep()
        : base(id: ProcessConstants.EndStepName, null)
    {
    }

    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        // The end step has no functions.
        return [];
    }

    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder, KernelProcessStepStateMetadata? stateMetadata = null)
    {
        // The end step has no state.
        return new KernelProcessStepInfo(typeof(KernelProcessStepState), new KernelProcessStepState(ProcessConstants.EndStepName, version: ProcessConstants.InternalStepsVersion), []);
    }
}
