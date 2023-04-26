// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
namespace Microsoft.SemanticKernel;

public static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Adds a <see cref="IChatCompletion"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The ITextEmbeddingService instance.</param>
    /// <param name="setAsDefault">Optional: set as the default IChatCompletionService</param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        IChatCompletion instance,
        bool setAsDefault = false)
            => services.SetService<IChatCompletion>(serviceId, instance, setAsDefault);

    /// <summary>
    /// Adds a <see cref="IChatCompletion"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates IChatCompletionService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default IChatCompletionService</param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<IChatCompletion> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<IChatCompletion>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Adds a <see cref="IChatCompletion"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="IChatCompletion"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="IChatCompletion"/></param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, IChatCompletion> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<IChatCompletion>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Set the <see cref="IChatCompletion"/> to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of <see cref="IChatCompletion"/> to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultChatCompletionService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<IChatCompletion>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"Chat completion service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="IChatCompletion"/> matching the given <paramref name="serviceId"/>, or
    /// the default if <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The completion service id matching the given id or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static IChatCompletion GetChatCompletionServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null) => services.GetNamedServiceOrDefault<IChatCompletion>(serviceId)
            ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Chat completion service not found");

    /// <summary>
    /// Remove the <see cref="IChatCompletion"/> with the given <paramref name="serviceId"/>.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveChatCompletionService(
        this INamedServiceCollection services,
        string serviceId)
            => services.TryRemove<IChatCompletion>(serviceId);

    /// <summary>
    /// Remove all <see cref="IChatCompletion"/> services.
    /// </summary>
    public static void RemoveAllChatCompletionServices(
        this INamedServiceCollection services)
            => services.Clear<IChatCompletion>();

    /// <summary>
    /// Get all <see cref="IChatCompletion"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetChatCompletionServiceIds(
        this INamedServiceProvider services)
            => services.GetServiceNames<IChatCompletion>();

    /// <summary>
    /// Gets the default <see cref="IChatCompletion"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="IChatCompletion"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultChatCompletionServiceId(
        this INamedServiceProvider services)
            => services.GetDefaultServiceName<IChatCompletion>();

    /// <summary>
    /// Returns true if a <see cref="IChatCompletion"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasChatCompletionService(
        this INamedServiceProvider services,
        string? serviceId = null)
            => services.HasServiceName<IChatCompletion>(serviceId);
}
