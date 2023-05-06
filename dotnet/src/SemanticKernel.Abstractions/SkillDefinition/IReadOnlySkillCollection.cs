// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Read-only skill collection interface.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public interface IReadOnlySkillCollection
{
    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetFunction(string functionName);

    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetFunction(string skillName, string functionName);

    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Gets the function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Gets the semantic function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetSemanticFunction(string functionName);

    /// <summary>
    /// Gets the semantic function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetSemanticFunction(string skillName, string functionName);

    /// <summary>
    /// Gets the semantic function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetSemanticFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Gets the semantic function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetSemanticFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Gets the native function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetNativeFunction(string functionName);

    /// <summary>
    /// Gets the native function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <returns>The function retrieved from the collection.</returns>
    /// <exception cref="KernelException">The specified function could not be found in the collection.</exception>
    ISKFunction GetNativeFunction(string skillName, string functionName);

    /// <summary>
    /// Gets the native function stored in the collection.
    /// </summary>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetNativeFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Gets the native function stored in the collection.
    /// </summary>
    /// <param name="skillName">The name of the skill with which the function is associated.</param>
    /// <param name="functionName">The name of the function to retrieve.</param>
    /// <param name="functionInstance">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/>.</param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    bool TryGetNativeFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance);

    /// <summary>
    /// Get all registered functions details, minus the delegates
    /// </summary>
    /// <param name="includeSemantic">Whether to include semantic functions in the list</param>
    /// <param name="includeNative">Whether to include native functions in the list</param>
    /// <returns>An object containing all the functions details</returns>
    FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true);
}
