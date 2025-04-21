// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Provides extension methods for managing and registering agents within an <see cref="IAgentRuntime"/>.
/// </summary>
public static class AgentRuntimeExtensions
{
    internal const string DirectMessageTopicSuffix = ":";

    /// <summary>
    /// Registers an agent type with the runtime, providing a factory function to create instances of the agent.
    /// </summary>
    /// <typeparam name="TAgent">The type of agent being registered. Must implement <see cref="IHostableAgent"/>.</typeparam>
    /// <param name="runtime">The <see cref="IAgentRuntime"/> where the agent will be registered.</param>
    /// <param name="type">The <see cref="AgentType"/> representing the type of agent.</param>
    /// <param name="serviceProvider">The service provider used for dependency injection.</param>
    /// <param name="additionalArguments">Additional arguments to pass to the agent's constructor.</param>
    /// <returns>A <see cref="ValueTask{AgentType}"/> representing the asynchronous operation of registering the agent.</returns>
    public static ValueTask<AgentType> RegisterAgentTypeAsync<TAgent>(this IAgentRuntime runtime, AgentType type, IServiceProvider serviceProvider, params object[] additionalArguments)
        where TAgent : BaseAgent
        => RegisterAgentTypeAsync(runtime, type, typeof(TAgent), serviceProvider, additionalArguments);

    /// <summary>
    /// Registers an agent type with the runtime using the specified runtime type and additional constructor arguments.
    /// </summary>
    /// <param name="runtime">The agent runtime instance to register the agent with.</param>
    /// <param name="type">The agent type to register.</param>
    /// <param name="runtimeType">The .NET type of the agent to activate.</param>
    /// <param name="serviceProvider">The service provider for dependency injection.</param>
    /// <param name="additionalArguments">Additional arguments to pass to the agent's constructor.</param>
    /// <returns>A <see cref="ValueTask{AgentType}"/> representing the asynchronous registration operation containing the registered agent type.</returns>
    public static ValueTask<AgentType> RegisterAgentTypeAsync(this IAgentRuntime runtime, AgentType type, Type runtimeType, IServiceProvider serviceProvider, params object[] additionalArguments)
    {
        ValueTask<IHostableAgent> factory(AgentId id, IAgentRuntime runtime) => ActivateAgentAsync(serviceProvider, runtimeType, [id, runtime, .. additionalArguments]);

        return runtime.RegisterAgentFactoryAsync(type, factory);
    }

    /// <summary>
    /// Registers implicit subscriptions for an agent type based on the type's custom attributes.
    /// </summary>
    /// <typeparam name="TAgent">The type of the agent.</typeparam>
    /// <param name="runtime">The agent runtime instance.</param>
    /// <param name="type">The agent type to register subscriptions for.</param>
    /// <param name="skipClassSubscriptions">If true, class-level subscriptions are skipped.</param>
    /// <param name="skipDirectMessageSubscription">If true, the direct message subscription is skipped.</param>
    /// <returns>A <see cref="ValueTask"/> representing the asynchronous subscription registration operation.</returns>
    public static ValueTask RegisterImplicitAgentSubscriptionsAsync<TAgent>(this IAgentRuntime runtime, AgentType type, bool skipClassSubscriptions = false, bool skipDirectMessageSubscription = false)
        where TAgent : BaseAgent
        => RegisterImplicitAgentSubscriptionsAsync(runtime, type, typeof(TAgent), skipClassSubscriptions, skipDirectMessageSubscription);

    /// <summary>
    /// Registers implicit subscriptions for the specified agent type using runtime type information.
    /// </summary>
    /// <param name="runtime">The agent runtime instance.</param>
    /// <param name="type">The agent type for which to register subscriptions.</param>
    /// <param name="runtimeType">The .NET type of the agent.</param>
    /// <param name="skipClassSubscriptions">If true, class-level subscriptions are not registered.</param>
    /// <param name="skipDirectMessageSubscription">If true, the direct message subscription is not registered.</param>
    /// <returns>A <see cref="ValueTask"/> representing the asynchronous subscription registration operation.</returns>
    public static async ValueTask RegisterImplicitAgentSubscriptionsAsync(this IAgentRuntime runtime, AgentType type, Type runtimeType, bool skipClassSubscriptions = false, bool skipDirectMessageSubscription = false)
    {
        ISubscriptionDefinition[] subscriptions = BindSubscriptionsForAgentType(type, runtimeType, skipClassSubscriptions, skipDirectMessageSubscription);
        foreach (ISubscriptionDefinition subscription in subscriptions)
        {
            await runtime.AddSubscriptionAsync(subscription).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Binds subscription definitions for the given agent type based on the custom attributes applied to the runtime type.
    /// </summary>
    /// <param name="agentType">The agent type to bind subscriptions for.</param>
    /// <param name="runtimeType">The .NET type of the agent.</param>
    /// <param name="skipClassSubscriptions">If true, class-level subscriptions are skipped.</param>
    /// <param name="skipDirectMessageSubscription">If true, the direct message subscription is skipped.</param>
    /// <returns>An array of subscription definitions for the agent type.</returns>
    private static ISubscriptionDefinition[] BindSubscriptionsForAgentType(AgentType agentType, Type runtimeType, bool skipClassSubscriptions = false, bool skipDirectMessageSubscription = false)
    {
        List<ISubscriptionDefinition> subscriptions = [];

        if (!skipClassSubscriptions)
        {
            subscriptions.AddRange(runtimeType.GetCustomAttributes<TypeSubscriptionAttribute>().Select(t => t.Bind(agentType)));

            subscriptions.AddRange(runtimeType.GetCustomAttributes<TypePrefixSubscriptionAttribute>().Select(t => t.Bind(agentType)));
        }

        if (!skipDirectMessageSubscription)
        {
            // Direct message subscription using agent name as prefix.
            subscriptions.Add(new TypePrefixSubscription(agentType.Name + DirectMessageTopicSuffix, agentType));
        }

        return [.. subscriptions];
    }

    /// <summary>
    /// Instantiates and activates an agent asynchronously using dependency injection.
    /// </summary>
    /// <param name="serviceProvider">The service provider used for dependency injection.</param>
    /// <param name="runtimeType">The .NET type of the agent being activated.</param>
    /// <param name="additionalArguments">Additional arguments to pass to the agent's constructor.</param>
    /// <returns>A <see cref="ValueTask{T}"/> representing the asynchronous activation of the agent.</returns>
    private static ValueTask<IHostableAgent> ActivateAgentAsync(IServiceProvider serviceProvider, Type runtimeType, params object[] additionalArguments)
    {
        try
        {
            IHostableAgent agent = (BaseAgent)ActivatorUtilities.CreateInstance(serviceProvider, runtimeType, additionalArguments);

#if !NETCOREAPP
            return agent.AsValueTask();
#else
            return ValueTask.FromResult(agent);
#endif
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
#if !NETCOREAPP
            return e.AsValueTask<IHostableAgent>();
#else
            return ValueTask.FromException<IHostableAgent>(e);
#endif
        }
    }
}
