// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A serializable representation of an edge between a source Step and a <see cref="ProcessFunctionTarget"/>.
/// </summary>
public record ProcessEdge
{
    /// <summary>
    /// The unique identifier of the source Step.
    /// </summary>
    public string SourceId { get; set; }

    /// <summary>
    /// The collection of <see cref="ProcessFunctionTarget"/>s that are the output of the source Step.
    /// </summary>
    public IEnumerable<ProcessFunctionTarget> OutputTargets { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessEdge"/> class.
    /// </summary>
    /// <param name="sourceId">The unique identifier of the source Step.</param>
    /// <param name="outputTargets">The collection of <see cref="ProcessFunctionTarget"/>s that are the output of the source Step.</param>
    public ProcessEdge(string sourceId, IEnumerable<ProcessFunctionTarget> outputTargets)
    {
        this.SourceId = sourceId;
        this.OutputTargets = outputTargets;
    }
}
