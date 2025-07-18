// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Process step builder for a delegate step.
/// </summary>
public class ProcessDelegateBuilder : ProcessStepBuilder
{
    private readonly StepFunction _stepFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessDelegateBuilder"/> class.
    /// </summary>
    /// <param name="id"></param>
    /// <param name="stepFunction"></param>
    /// <param name="processBuilder"></param>
    public ProcessDelegateBuilder(string id, StepFunction stepFunction, ProcessBuilder? processBuilder) : base(id, processBuilder)
    {
        this._stepFunction = stepFunction ?? throw new ArgumentNullException(nameof(stepFunction), "Step function cannot be null.");
    }

    internal override KernelProcessStepInfo BuildStep(ProcessBuilder processBuilder, KernelProcessStepStateMetadata? stateMetadata = null) // %%% METADATA ???
    {
        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());

        KernelProcessStepState stateObject = new(this.Name, "none", this.Id); // %%% VERSION IS NOT USED, BUT REQUIRED BY THE BASE CLASS

        return new KernelProcessDelegateStepInfo(stateObject, this._stepFunction, builtEdges);
    }

    internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
    {
        // Nothing to do here, as this is a delegate step
        return [];
    }
}
