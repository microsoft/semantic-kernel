// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Provides a fluent API to configure and build an <see cref="AgentsApp"/> instance.
/// </summary>
public class AgentsAppBuilder
{
    private readonly HostApplicationBuilder _builder;
    private readonly List<Func<AgentsApp, ValueTask<AgentType>>> _agentTypeRegistrations;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentsAppBuilder"/> class using the specified <see cref="HostApplicationBuilder"/>.
    /// </summary>
    /// <param name="baseBuilder">An optional host application builder to use; if null, a new instance is created.</param>
    public AgentsAppBuilder(HostApplicationBuilder? baseBuilder = null)
    {
        this._builder = baseBuilder ?? new HostApplicationBuilder();
        this._agentTypeRegistrations = [];
    }

    /// <summary>
    /// Gets the dependency injection service collection.
    /// </summary>
    public IServiceCollection Services => this._builder.Services;

    /// <summary>
    /// Gets the application's configuration.
    /// </summary>
    public IConfiguration Configuration => this._builder.Configuration;

    /// <summary>
    /// Scans all assemblies loaded in the current application domain to register available agents.
    /// </summary>
    public void AddAgentsFromAssemblies()
    {
        this.AddAgentsFromAssemblies(AppDomain.CurrentDomain.GetAssemblies());
    }

    /// <summary>
    /// Configures the AgentsApp to use the specified agent runtime.
    /// </summary>
    /// <typeparam name="TRuntime">The type of the runtime.</typeparam>
    /// <param name="runtime">The runtime instance to use.</param>
    /// <returns>The modified instance of <see cref="AgentsAppBuilder"/>.</returns>
    public AgentsAppBuilder UseRuntime<TRuntime>(TRuntime runtime) where TRuntime : class, IAgentRuntime
    {
        this.Services.AddSingleton<IAgentRuntime>(_ => runtime);
        this.Services.AddHostedService(services => runtime);

        return this;
    }

    /// <summary>
    /// Registers agents from the provided assemblies.
    /// </summary>
    /// <param name="assemblies">An array of assemblies to scan for agents.</param>
    /// <returns>The modified instance of <see cref="AgentsAppBuilder"/>.</returns>
    public AgentsAppBuilder AddAgentsFromAssemblies(params Assembly[] assemblies)
    {
        IEnumerable<Type> agentTypes =
            assemblies.SelectMany(assembly => assembly.GetTypes())
                .Where(
                    type =>
                        typeof(BaseAgent).IsAssignableFrom(type) &&
                        !type.IsAbstract);

        foreach (Type agentType in agentTypes)
        {
            // TODO: Expose skipClassSubscriptions and skipDirectMessageSubscription as parameters?
            this.AddAgent(agentType.Name, agentType);
        }

        return this;
    }

    /// <summary>
    /// Registers an agent of type <typeparamref name="TAgent"/> with the associated agent type and subscription options.
    /// </summary>
    /// <typeparam name="TAgent">The .NET type of the agent.</typeparam>
    /// <param name="agentType">The agent type identifier.</param>
    /// <param name="skipClassSubscriptions">Option to skip class subscriptions.</param>
    /// <param name="skipDirectMessageSubscription">Option to skip direct message subscriptions.</param>
    /// <returns>The modified instance of <see cref="AgentsAppBuilder"/>.</returns>
    public AgentsAppBuilder AddAgent<TAgent>(AgentType agentType, bool skipClassSubscriptions = false, bool skipDirectMessageSubscription = false) where TAgent : IHostableAgent
        => this.AddAgent(agentType, typeof(TAgent), skipClassSubscriptions, skipDirectMessageSubscription);

    /// <summary>
    /// Builds the AgentsApp instance by constructing the host and registering all agent types.
    /// </summary>
    /// <returns>A task representing the asynchronous operation, returning the built <see cref="AgentsApp"/>.</returns>
    public async ValueTask<AgentsApp> BuildAsync()
    {
        IHost host = this._builder.Build();

        AgentsApp app = new(host);

        foreach (Func<AgentsApp, ValueTask<AgentType>> registration in this._agentTypeRegistrations)
        {
            await registration(app).ConfigureAwait(false);
        }

        return app;
    }

    /// <summary>
    /// Registers an agent with the runtime using the specified agent type and runtime type.
    /// </summary>
    /// <param name="agentType">The agent type identifier.</param>
    /// <param name="runtimeType">The .NET type representing the agent.</param>
    /// <param name="skipClassSubscriptions">Option to skip class subscriptions.</param>
    /// <param name="skipDirectMessageSubscription">Option to skip direct message subscriptions.</param>
    /// <returns>The modified instance of <see cref="AgentsAppBuilder"/>.</returns>
    private AgentsAppBuilder AddAgent(AgentType agentType, Type runtimeType, bool skipClassSubscriptions = false, bool skipDirectMessageSubscription = false)
    {
        this._agentTypeRegistrations.Add(
            async app =>
            {
                await app.AgentRuntime.RegisterAgentTypeAsync(agentType, runtimeType, app.Services).ConfigureAwait(false);

                await app.AgentRuntime.RegisterImplicitAgentSubscriptionsAsync(agentType, runtimeType, skipClassSubscriptions, skipDirectMessageSubscription).ConfigureAwait(false);

                return agentType;
            });

        return this;
    }
}
