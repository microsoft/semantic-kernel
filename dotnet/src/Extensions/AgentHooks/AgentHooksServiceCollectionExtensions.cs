// Copyright (c) Microsoft. All rights reserved.

using System;
using AgentHooks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace Microsoft.SemanticKernel.AgentHooks;

/// <summary>
/// Service collection extensions wiring the AGENT-HOOKS-0.1 adapter into a
/// kernel's filter pipeline.
/// </summary>
public static class AgentHooksServiceCollectionExtensions
{
    /// <summary>
    /// Registers the agent-hooks adapter as function-invocation, prompt-render,
    /// and auto-function-invocation filters. Interceptors are resolved from the
    /// container: register implementations of <see cref="IInterceptor"/> before
    /// building the kernel.
    /// </summary>
    public static IServiceCollection AddAgentHooks(
        this IServiceCollection services, Action<AgentHooksOptions>? configure = null)
    {
        var options = new AgentHooksOptions();
        configure?.Invoke(options);
        services.TryAddSingleton(options);
        services.TryAddSingleton<AgentHooksFilter>();
        services.AddSingleton<IFunctionInvocationFilter>(sp => sp.GetRequiredService<AgentHooksFilter>());
        services.AddSingleton<IPromptRenderFilter>(sp => sp.GetRequiredService<AgentHooksFilter>());
        services.AddSingleton<IAutoFunctionInvocationFilter>(sp => sp.GetRequiredService<AgentHooksFilter>());
        return services;
    }
}
