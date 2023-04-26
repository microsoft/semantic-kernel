// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Services;

// Use base namespace for better discoverability and to avoid conflicts with other extensions.
namespace Microsoft.SemanticKernel;

public static class TextCompletionServiceExtensions
{
    /// <summary>
    /// Adds a <see cref="ITextCompletion"/> instance to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <see cref="ITextCompletion"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletion"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        ITextCompletion instance,
        bool setAsDefault = false)
            => services.SetService<ITextCompletion>(serviceId, instance, setAsDefault);

    /// <summary>
    /// Adds a <see cref="ITextCompletion"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextCompletion"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletion"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<ITextCompletion> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<ITextCompletion>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Adds a <see cref="ITextCompletion"/> factory method to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates <see cref="ITextCompletion"/> instances.</param>
    /// <param name="setAsDefault">Optional: set as the default <see cref="ITextCompletion"/></param>
    public static void AddTextCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, ITextCompletion> factory,
        bool setAsDefault = false)
            => services.SetServiceFactory<ITextCompletion>(serviceId, factory, setAsDefault);

    /// <summary>
    /// Set the default <see cref="ITextCompletion"/> service to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of completion service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    public static INamedServiceCollection SetDefaultTextCompletionService(
        this INamedServiceCollection services,
        string serviceId)
    {
        if (!services.TrySetDefault<ITextCompletion>(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"Text completion service id '{serviceId}' doesn't exist");
        }

        return services;
    }

    /// <summary>
    /// Get the <see cref="ITextCompletion"/> matching the given <paramref name="serviceId"/>, or the default
    /// if the <paramref name="serviceId"/> is not provided or not found.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The text completion service id matching the given ID or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable service is found.</exception>
    public static ITextCompletion GetTextCompletionServiceOrDefault(
        this INamedServiceProvider services,
        string? serviceId = null) => services.GetService<ITextCompletion>()
            ?? throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "Text completion service not found");

    /// <summary>
    /// Remove the <see cref="ITextCompletion"/> with the given <paramref name="serviceId"/>.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveTextCompletionService(
        this INamedServiceCollection services, string serviceId)
            => services.TryRemove<ITextCompletion>(serviceId);

    /// <summary>
    /// Unregisters all <see cref="ITextCompletion"/> services.
    /// </summary>
    /// <param name="services">The service collection.</param>
    public static void RemoveAllTextCompletionServices(
        this INamedServiceCollection services)
            => services.Clear<ITextCompletion>();

    /// <summary>
    /// Get all registered <see cref="ITextCompletion"/> service IDs.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetTextCompletionServiceIds(
        this INamedServiceProvider services)
            => services.GetServiceNames<ITextCompletion>();

    /// <summary>
    /// Gets the default <see cref="ITextCompletion"/> ID, or null none are registered or set as default.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <returns>The service ID of the default <see cref="ITextCompletion"/>, or null if none are registered
    /// or set as default.</returns>
    public static string? GetDefaultTextCompletionServiceId(
        this INamedServiceProvider services)
            => services.GetDefaultServiceName<ITextCompletion>();

    /// <summary>
    /// Returns true if a <see cref="ITextCompletion"/> exist with the specified ID.
    /// </summary>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">The service ID to search for. If null, it will look for a default service.</param>
    /// <returns>True if the service ID is registered, false otherwise.</returns>
    public static bool HasTextCompletionService(
        this INamedServiceProvider services,
        string? serviceId = null)
            => services.HasServiceName<ITextCompletion>(serviceId);
}
