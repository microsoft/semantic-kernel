// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// EndStep is a special purpose step that is used to trigger a process to stop. It is the last step in a process.
/// </summary>
internal sealed class EndStep : ProcessStepBuilder
{
    private const string EndStepValue = "Microsoft.SemanticKernel.Process.EndStep";

    /// <summary>
    /// The name of the end step.
    /// </summary>
    public const string EndStepName = EndStepValue;

    /// <summary>
    /// The event ID for stopping a process.
    /// </summary>
    public const string EndStepId = EndStepValue;

    /// <summary>
    /// The static instance of the <see cref="EndStep"/> class.
    /// </summary>
    public static EndStep Instance { get; } = new EndStep();

    /// <summary>
    /// Represents the end of a process.
    /// </summary>
    internal EndStep()
        : base(EndStepName)
    {
    }

    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        // The end step has no functions.
        return [];
    }

    internal override KernelProcessStepInfo BuildStep()
    {
        // The end step has no state.
        return new KernelProcessStepInfo(typeof(KernelProcessStepState), new KernelProcessStepState(EndStepName), []);
    }
}
