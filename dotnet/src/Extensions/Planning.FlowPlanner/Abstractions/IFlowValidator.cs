// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

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
