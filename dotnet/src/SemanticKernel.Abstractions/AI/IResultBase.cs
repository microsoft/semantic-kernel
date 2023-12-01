// Copyright (c) Microsoft. All rights reserved.

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
