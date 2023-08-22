// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Provides extension methods for working with chat completion services.
/// </summary>
/// <example>
/// <code>
/// IAIServiceProvider serviceProvider = ...;
/// IChatCompletion chatCompletionService = serviceProvider.GetChatCompletionService();
/// </code>
/// </example>
public static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Get the <see cref="IChatCompletion"/> matching the given <paramref name="serviceId"/>, or
    /// the default if <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The completion service id matching the given id or the default.</returns>
    /// <exception cref="SKException">Thrown when no suitable service is found.</exception>
    public static IChatCompletion GetChatCompletionService(
        this IAIServiceProvider services,
        string? serviceId = null) => services.GetService<IChatCompletion>(serviceId)
            ?? throw new SKException("Chat completion service not found");

    /// <summary>
    /// Returns true if a <see cref="IChatCompletion"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasChatCompletionService(
        this IAIServiceProvider services,
        string? serviceId = null)
            => services.TryGetService<IChatCompletion>(serviceId, out _);
}
