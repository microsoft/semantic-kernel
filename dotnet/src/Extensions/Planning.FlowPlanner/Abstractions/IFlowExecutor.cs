// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;

#pragma warning restore IDE0130 // Namespace does not match folder structure

using Microsoft.SemanticKernel.Orchestration;
using System.Threading.Tasks;

/// <summary>
/// Flow executor interface
/// </summary>
public interface IFlowExecutor
{
    /// <summary>
    /// Execute the <see cref="Flow"/>
    /// </summary>
    /// <param name="flow">Flow</param>
    /// <param name="sessionId">Session id, which is used to track the execution status.</param>
    /// <param name="input">The input from client to continue the execution.</param>
    /// <param name="contextVariables">The key value pair of contextVariable </param>
    /// <returns>The execution context</returns>
    Task<SKContext> ExecuteAsync(Flow flow, string sessionId, string input, ContextVariables contextVariables);
}