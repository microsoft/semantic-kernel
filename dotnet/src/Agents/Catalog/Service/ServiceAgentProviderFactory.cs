// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// This factory provides the entry point for hosting a <see cref="ServiceAgent"/>
/// to instantiate and utilize an agent via its <see cref="ServiceAgentProvider"/>,
/// regardless of the shape of the constructor on any <see cref="Agent"/> subclasss.
/// </summary>
public static class ServiceAgentProviderFactory
{
    private const string ServiceProviderTypePropertyName = nameof(ServiceAgentProviderAttribute<ServiceAgentProvider>.ServiceProviderType);
    private static readonly string ServiceProviderAttributeName = typeof(ServiceAgentProviderAttribute<>).Name;

    /// <summary>
    /// Enumerate all the <see cref="ServiceAgent"/> types in the specified assembly
    /// that available for invocation.
    /// </summary>
    /// <param name="assembly">The specified assembly</param>
    /// <returns>An enumeration of all <see cref="ServiceAgent"/> types available for invocation</returns>
    public static IEnumerable<Type> GetAgentTypes(Assembly assembly)
    {
        foreach (Type type in assembly.GetTypes())
        {
            if (typeof(ServiceAgent).IsAssignableFrom(type) &&
                !type.IsAbstract &&
                type.GetCustomAttribute(typeof(ServiceAgentProviderAttribute<>)) != null)
            {
                yield return type;
            }
        }
    }

    /// <summary>
    /// Creates the <see cref="ServiceAgentProvider"/> associated with a <see cref="ServiceAgent"/>.
    /// </summary>
    /// <param name="agentType">The type of the specific <see cref="ServiceAgent"/>.</param>
    /// <param name="configuration">The active configuration.</param>
    /// <param name="loggerFactory">The logging services for the <see cref="ServiceAgent"/>.</param>
    /// <returns>A <see cref="ServiceAgentProvider"/> associated with the requested agent <see cref="Type"/>.</returns>
    public static ServiceAgentProvider CreateServicesProvider(Type agentType, IConfiguration configuration, ILoggerFactory loggerFactory)
    {
        Verify.NotNull(configuration, nameof(configuration));
        Verify.NotNull(loggerFactory, nameof(loggerFactory));
        Verify.NotNull(agentType, nameof(agentType));

        VerifyTypeIsServiceAgent(agentType);

        Attribute providerAttribute =
            agentType.GetCustomAttribute(typeof(ServiceAgentProviderAttribute<>)) ??
            throw new NotSupportedException($"Specified agent type, {agentType.Name}, is not associated with the expected attribute: {ServiceProviderAttributeName}");

        Type providerType =
            providerAttribute.GetType().GetProperty(ServiceProviderTypePropertyName)?.GetValue(providerAttribute) as Type ??
            throw new InvalidOperationException($"Unable to read the property value for {ServiceProviderAttributeName}.{ServiceProviderTypePropertyName} from the attribute associated with {agentType.Name}");

        if (!typeof(ServiceAgentProvider).IsAssignableFrom(providerType))
        {
            throw new NotSupportedException($"The specified service provider does not derive from {nameof(ServiceAgentProvider)}.");
        }

        return
            Activator.CreateInstance(providerType, configuration, loggerFactory) as ServiceAgentProvider ??
            throw new TypeAccessException($"Unable to create {nameof(ServiceAgentProvider)} instance of type {providerType.Name}.");
    }

    private static void VerifyTypeIsServiceAgent(Type agentType)
    {
        if (!typeof(ServiceAgent).IsAssignableFrom(agentType))
        {
            throw new ArgumentException(
                $"The provided type does not derive from {nameof(ServiceAgent)}.",
                nameof(agentType));
        }
    }
}
