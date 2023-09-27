// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System.Collections.Generic;
using System.Threading.Tasks;

/// <summary>
/// Interface for flow catalog, which provides functionality of flow registration, enumeration and search.
/// </summary>
public interface IFlowCatalog
{
    /// <summary>
    /// Get all <see cref="Flow"/> instances from the repository
    /// </summary>
    /// <returns>flows</returns>
    Task<IEnumerable<Flow>> GetFlowsAsync();

    /// <summary>
    /// Get <see cref="Flow"/> by name
    /// </summary>
    /// <param name="flowName">the flow name</param>
    /// <returns>flow given the name</returns>
    Task<Flow?> GetFlowAsync(string flowName);

    /// <summary>
    /// Register flow in the catalog
    /// </summary>
    /// <param name="flow">flow</param>
    /// <returns></returns>
    Task<bool> RegisterFlowAsync(Flow flow);
}
