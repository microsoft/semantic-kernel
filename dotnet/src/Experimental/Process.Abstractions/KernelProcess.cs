// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed class KernelProcess : KernelProcessStep<KernelProcessState>
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public IList<KernelProcessStepBase> Steps { get; private init; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="name">The human friendly name of the Process.</param>
    /// <param name="steps">The steps of the process.</param>
    public KernelProcess(string name, IList<KernelProcessStepBase> steps)
    {
        Verify.NotNull(steps);
        Verify.NotNullOrWhiteSpace(name);

        this.Steps = [];
        this.Steps.AddRange(steps);
        this.State.State = new KernelProcessState
        {
            Name = name
        };
    }
}
