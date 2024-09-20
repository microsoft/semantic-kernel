// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public record Process : ProcessStep
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public List<ProcessStep> Steps { get; set; }

    /// <summary>
    /// The unique identifier of the Step that is defined as the entry point to the process.
    /// </summary>
    public string EntryPointId { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="Process"/> class.
    /// </summary>
    /// <param name="id">The unique Id of the <see cref="Process"/>.</param>
    /// <param name="name">The human friendly name of the Process.</param>
    /// <param name="stepType">The assembly qualified name of the Step type.</param>
    /// <param name="state">The state object associated with the Process.</param>
    /// <param name="steps">The collection of Steps in the Process.</param>
    /// <param name="entryPointId">The unique identifier of the Step that is defined as the entry point to the process.</param>
    public Process(string? id, string name, string stepType, object state, List<ProcessStep> steps, string entryPointId)
        : base(id, name, stepType, state)
    {
        this.Steps = steps;
        this.EntryPointId = entryPointId;
    }
}
