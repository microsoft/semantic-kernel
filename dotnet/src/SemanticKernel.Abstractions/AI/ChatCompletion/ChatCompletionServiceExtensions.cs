// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Adds a <see cref="IChatCompletionService"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The ITextEmbeddingGenerationService instance.</param>
    /// <param name="setAsDefault">Optional: set as the default IChatCompletionService</param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        IChatCompletionService instance,
        bool setAsDefault = false)
    {
        services.SetSingleton<IChatCompletionService>(serviceId, instance);
    }

    /// <summary>
    /// Adds a <see cref="IChatCompletionService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates IChatCompletionService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default IChatCompletionService</param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<IChatCompletionService> factory,
        bool setAsDefault = false)
    {
        services.SetTransient<IChatCompletionService>(serviceId, factory, setAsDefault);

    }

    /// <summary>
    /// Adds a <see cref="IChatCompletionService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="IChatCompletionService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="IChatCompletionService"/></param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, IChatCompletionService> factory,
        bool setAsDefault = false)
    {
        services.SetTransient<IChatCompletionService>(serviceId, factory, setAsDefault);
    }

    /// <summary>
    /// Set the <see cref="IChatCompletionService"/> to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of <see cref="IChatCompletionService"/> to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultChatCompletionService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<IChatCompletionService>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"Chat completion service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="IChatCompletionService"/> matching the given <paramref name="serviceId"/>, or
    /// the default if <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The completion service id matching the given id or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static IChatCompletionService GetChatCompletionServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null)
    {
        return services.GetNamedServiceOrDefault<IChatCompletionService>(serviceId)
            ?? throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "Chat completion service not found");
    }

    /// <summary>
    /// Remove the <see cref="IChatCompletionService"/> with the given <paramref name="serviceId"/>.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveChatCompletionService(this INamedServiceCollection services, string serviceId)
    {
        return services.TryRemove<IChatCompletionService>(serviceId);
    }

    /// <summary>
    /// Remove all <see cref="IChatCompletionService"/> services.
    /// </summary>
    public static void RemoveAllChatCompletionServices(this INamedServiceCollection services)
    {
        services.Clear<IChatCompletionService>();
    }

    /// <summary>
    /// Get all <see cref="IChatCompletionService"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetChatCompletionServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<IChatCompletionService>();
    }

    /// <summary>
    /// Gets the default <see cref="IChatCompletionService"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="IChatCompletionService"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultChatCompletionServiceId(this INamedServiceProvider services)
    {
        return services.GetDefaultServiceName<IChatCompletionService>();
    }
}
