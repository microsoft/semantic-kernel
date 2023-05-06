// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Class that holds extension methods for ContextVariables.
/// </summary>
public static class ContextVariablesExtensions
{
    /// <summary>
    /// Simple extension method to turn a string into a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="text">The text to transform</param>
    /// <returns>An instance of <see cref="ContextVariables"/></returns>
    public static ContextVariables ToContextVariables(this string text)
    {
        return new ContextVariables(text);
    }
}
