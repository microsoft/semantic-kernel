// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Provides extension methods for working with <see cref="ITextCompletion"/> services.
/// </summary>
public static class TextCompletionServiceExtensions
{
    /// <summary>
    /// Get the <see cref="ITextCompletion"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The text completion service id matching the given ID or the default.</returns>
    /// <exception cref="SKException">Thrown when no suitable service is found.</exception>
    public static ITextCompletion GetTextCompletionServiceOrDefault(
        this IAIServiceProvider services,
        string? serviceId = null) => services.GetService<ITextCompletion>(serviceId)
            ?? throw new SKException("Text completion service not found");

    /// <summary>
    /// Returns true if a <see cref="ITextCompletion"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasTextCompletionService(
        this IAIServiceProvider services,
        string? serviceId = null)
            => services.TryGetService<ITextCompletion>(serviceId, out _);
}
