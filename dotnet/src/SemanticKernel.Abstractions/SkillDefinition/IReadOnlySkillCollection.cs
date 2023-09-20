// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Read-only skill collection interface.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
public interface IReadOnlySkillCollection
{
    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="SKException">The specified function could not be found in the collection.</exception>
    ISKFunction GetFunction(string functionName);

    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="SKException">The specified function could not be found in the collection.</exception>
    ISKFunction GetFunction(string skillName, string functionName);

    /// <summary>
    /// Check if a function is available in the current context, and return it.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="availableFunction">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction);

    /// <summary>
    /// Check if a function is available in the current context, and return it.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="availableFunction">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction);

    /// <summary>
    /// Get a snapshot all registered functions details, minus the delegates
    /// </summary>
    /// <returns>An object containing all the functions details</returns>
    IReadOnlyList<FunctionView> GetFunctionViews();
}
