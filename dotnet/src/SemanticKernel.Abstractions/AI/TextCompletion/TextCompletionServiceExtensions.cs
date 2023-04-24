// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

public static class TextCompletionServiceExtensions
{
    /// <summary>
    /// Adds a <see cref="ITextCompletionService"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <see cref="ITextCompletionService"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletionService"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        ITextCompletionService instance,
        bool setAsDefault = false)
    {
        services.SetSingleton<ITextCompletionService>(serviceId, instance, setAsDefault);
    }

    /// <summary>
    /// Adds a <see cref="ITextCompletionService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextCompletionService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletionService"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<ITextCompletionService> factory,
        bool setAsDefault = false)
    {
        services.SetTransient<ITextCompletionService>(serviceId, factory, setAsDefault);

    }

    /// <summary>
    /// Adds a <see cref="ITextCompletionService"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextCompletionService"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletionService"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, ITextCompletionService> factory,
        bool setAsDefault = false)
    {
        services.SetTransient<ITextCompletionService>(serviceId, factory, setAsDefault);
    }

    /// <summary>
    /// Set the default <see cref="ITextCompletionService"/> service to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of completion service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultTextCompletionService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<ITextCompletionService>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"Text completion service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="ITextCompletionService"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The text completion service id matching the given ID or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextCompletionService GetTextCompletionServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null)
    {
        return services.GetService<ITextCompletionService>()
            ?? throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "Text completion service not found");
    }

    /// <summary>
    /// Remove the <see cref="ITextCompletionService"/> with the given <paramref name="serviceId"/>.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveTextCompletionService(this INamedServiceCollection services, string serviceId)
    {
        return services.TryRemove<ITextCompletionService>(serviceId);
    }

    /// <summary>
    /// Unregisters all <see cref="ITextCompletionService"/> services.
    /// </summary>
    /// <param name="services">The service collection.</param>
    public static void RemoveAllTextCompletionServices(this INamedServiceCollection services)
    {
        services.Clear<ITextCompletionService>();
    }

    /// <summary>
    /// Get all registered <see cref="ITextCompletionService"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetTextCompletionServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<ITextCompletionService>();
    }

    /// <summary>
    /// Gets the default <see cref="ITextCompletionService"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="ITextCompletionService"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultTextCompletionServiceId(this INamedServiceProvider services)
    {
        return services.GetDefaultServiceName<ITextCompletionService>();
    }
}
