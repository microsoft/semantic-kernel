// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;

/// <summary>
/// Extensions for <see cref="Kernel"/>.
/// </summary>
internal static class KernelExtensions
{
    public static void ImportPluginFromAgent(this Kernel kernel, IAgent agent)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(agent, nameof(agent));

        var agentConversationPlugin = new KernelPlugin(agent.Name, agent.Description);

        agentConversationPlugin.AddFunctionFromMethod(async (string input) =>
        {
            var thread = agent.CreateThread(input);
            return await thread.InvokeAsync().ConfigureAwait(false);
        },
        functionName: "Ask",
        description: $"Resolves maths problems.",
        parameters: new KernelParameterMetadata[]
        {
            new("input")
            {
                IsRequired = true,
                ParameterType = typeof(string),
                DefaultValue = "",
                Description = "The word problem to solve in 2-3 sentences. Make sure to include all the input variables needed along with their values and units otherwise the math function will not be able to solve it."
            }
        }, returnParameter: new()
        {
            ParameterType = typeof(string),
            Description = "The response from the assistant."
        },
        loggerFactory: kernel.Services.GetService<LoggerFactory>());

        kernel.Plugins.Add(agentConversationPlugin);
    }
}
