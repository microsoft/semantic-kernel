// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;

/// <summary>
/// Extensions for <see cref="Kernel"/>.
/// </summary>
internal static class KernelExtensions
{
    /// <summary>
    /// Imports the agent's plugin into the kernel.
    /// </summary>
    /// <param name="kernel">The Kernel instance.</param>
    /// <param name="agent">The Agent to import.</param>
    /// <param name="model">The <see cref="AgentAssistantModel"/> instance.</param>
    public static void ImportPluginFromAgent(this Kernel kernel, IAgent agent, AgentAssistantModel model)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(model, nameof(model));
        Verify.NotNull(model.Agent, nameof(model.Agent));

        var agentConversationPlugin = new KernelPlugin(model.Agent.Name!, model.Agent.Description);

        agentConversationPlugin.AddFunctionFromMethod(async (string input, KernelArguments args) =>
        {
            if (!agent.AssistantThreads.TryGetValue(model.Agent, out var thread))
            {
                thread = model.Agent.CreateThread();
                agent.AssistantThreads.Add(model.Agent, thread);
            }

            return await thread.InvokeAsync(input).ConfigureAwait(false);
        },
        functionName: "Ask",
        description: model.Description,
        parameters: new KernelParameterMetadata[]
        {
            new("input")
            {
                IsRequired = true,
                ParameterType = typeof(string),
                DefaultValue = "",
                Description = model.InputDescription
            }
        }, returnParameter: new()
        {
            ParameterType = typeof(string),
            Description = "The response from the assistant."
        },
        loggerFactory: kernel.LoggerFactory);

        kernel.Plugins.Add(agentConversationPlugin);
    }
}
