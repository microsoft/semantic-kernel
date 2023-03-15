// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Read-only skill collection interface.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1710:Identifiers should have correct suffix", Justification = "It is a collection")]
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public interface IReadOnlySkillCollection
{
    /// <summary>
    /// Check if the collection contains the specified function in the global skill, regardless of the function type
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if the function exists, false otherwise</returns>
    bool HasFunction(string skillName, string functionName);

    /// <summary>
    /// Check if the collection contains the specified function, regardless of the function type
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <returns>True if the function exists, false otherwise</returns>
    bool HasFunction(string functionName);

    /// <summary>
    /// Check if a semantic function is registered
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <param name="skillName">Skill name</param>
    /// <returns>True if the function exists</returns>
    bool HasSemanticFunction(string skillName, string functionName);

    /// <summary>
    /// Check if a native function is registered
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <param name="skillName">Skill name</param>
    /// <returns>True if the function exists</returns>
    bool HasNativeFunction(string skillName, string functionName);

    /// <summary>
    /// Check if a native function is registered in the global skill
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <returns>True if the function exists</returns>
    bool HasNativeFunction(string functionName);

    /// <summary>
    /// Return the function delegate stored in the collection, regardless of the function type
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <returns>Function delegate</returns>
    ISKFunction GetFunction(string functionName);

    /// <summary>
    /// Return the function delegate stored in the collection, regardless of the function type
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <param name="skillName">Skill name</param>
    /// <returns>Function delegate</returns>
    ISKFunction GetFunction(string skillName, string functionName);

    /// <summary>
    /// Return the semantic function delegate stored in the collection
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <returns>Semantic function delegate</returns>
    ISKFunction GetSemanticFunction(string functionName);

    /// <summary>
    /// Return the semantic function delegate stored in the collection
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <param name="skillName">Skill name</param>
    /// <returns>Semantic function delegate</returns>
    ISKFunction GetSemanticFunction(string skillName, string functionName);

    /// <summary>
    /// Return the native function delegate stored in the collection
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <param name="skillName">Skill name</param>
    /// <returns>Native function delegate</returns>
    ISKFunction GetNativeFunction(string skillName, string functionName);

    /// <summary>
    /// Return the native function delegate stored in the collection
    /// </summary>
    /// <param name="functionName">Function name</param>
    /// <returns>Native function delegate</returns>
    ISKFunction GetNativeFunction(string functionName);

    /// <summary>
    /// Get all registered functions details, minus the delegates
    /// </summary>
    /// <param name="includeSemantic">Whether to include semantic functions in the list</param>
    /// <param name="includeNative">Whether to include native functions in the list</param>
    /// <returns>An object containing all the functions details</returns>
    FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true);
}
