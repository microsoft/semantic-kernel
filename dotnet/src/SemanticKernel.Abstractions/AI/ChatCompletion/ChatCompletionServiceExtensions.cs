// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Adds a chat completion service factory to the services collection
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
        services.AddSingleton<IChatCompletionService>(serviceId, instance);
    }

    /// <summary>
    /// Adds a chat completion service factory to the services collection
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
        services.AddTransient<IChatCompletionService>(serviceId, factory, setAsDefault);

    }

    /// <summary>
    /// Adds a chat completion service factory to the services collection
    /// </summary>
    /// <param name="services">The services collection</param>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates IChatCompletionService instances.</param>
    /// <param name="setAsDefault">Optional: set as the default IChatCompletionService</param>
    public static void AddChatCompletionService(
        this INamedServiceCollection services,
        string serviceId,
        Func<INamedServiceProvider, IChatCompletionService> factory,
        bool setAsDefault = false)
    {
        services.AddTransient<IChatCompletionService>(serviceId, factory, setAsDefault);
    }

    /// <summary>
    /// Set the default chat completion service to use for the kernel.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of text embedding service to use.</param>
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
    /// Get the chat completion service matching the given id or the default if an id is not provided or not found.
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
    /// Remove the chat completion service with the given id.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">Identifier of service to remove.</param>
    /// <returns>True if the service was found and removed. False otherwise</returns>
    public static bool TryRemoveChatCompletionService(this INamedServiceCollection services, string serviceId)
    {
        return services.TryRemove<IChatCompletionService>(serviceId);
    }

    /// <summary>
    /// Remove all chat completion services.
    /// </summary>
    public static void RemoveAllChatCompletionServices(this INamedServiceCollection services)
    {
        services.Clear<IChatCompletionService>();
    }

    /// <summary>
    /// Get all chat completion generation services.
    /// </summary>
    /// <param name="services">The service provider.</param>
    public static IEnumerable<string> GetChatCompletionServiceIds(this INamedServiceProvider services)
    {
        return services.GetServiceNames<IChatCompletionService>();
    }
}
