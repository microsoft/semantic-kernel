// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Indicates to Kernel that a ISKFunction can handle the given an event associated to the SKEventArg specialized type provided
/// </summary>
/// <typeparam name="TEventArgs">EventArgs support signature</typeparam>
public interface ISKFunctionEventSupport<TEventArgs> where TEventArgs : SKEventArgs
{
    /// <summary>
    /// Prepare the provided EventArguments type related to the ISKFunction event.
    /// </summary>
    /// <param name="context">SKContext state</param>
    /// <param name="eventArgs">Source EventArgs</param>
    /// <returns>EventArguments that the handler caller will get</returns>
    Task<TEventArgs> PrepareEventArgsAsync(SKContext context, TEventArgs? eventArgs = null);
}
