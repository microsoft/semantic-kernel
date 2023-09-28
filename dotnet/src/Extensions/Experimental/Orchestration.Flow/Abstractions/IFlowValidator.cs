// Copyright (c) Microsoft. All rights reserved.


namespace Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

/// <summary>
/// Flow validator interface
/// </summary>
public interface IFlowValidator
{
    /// <summary>
    /// Validate if the <see cref="Flow"/> is valid.
    /// </summary>
    /// <param name="flow"></param>
    void Validate(Flow flow);
}
