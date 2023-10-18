// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Interface for model results
/// </summary>
public interface IResultBase
{
    /// <summary>
    /// Gets the model result data.
    /// </summary>
    ModelResult ModelResult { get; }
}
