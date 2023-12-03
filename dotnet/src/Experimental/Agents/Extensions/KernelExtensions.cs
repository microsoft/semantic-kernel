// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;

/// <summary>
/// Extensions for <see cref="Kernel"/>.
/// </summary>
internal static class KernelExtensions
{
    public static void ImportPluginFromAgent(this Kernel kernel, AgentAssistantModel model)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(model, nameof(model));
        Verify.NotNull(model.Agent, nameof(model.Agent));

        var agentConversationPlugin = new KernelPlugin(model.Agent.Name, model.Agent.Description);

        agentConversationPlugin.AddFunctionFromMethod(async (string input) =>
        {
            var thread = model.Agent.CreateThread(input);
            return await thread.InvokeAsync().ConfigureAwait(false);
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
        loggerFactory: kernel.Services.GetService<LoggerFactory>());

        kernel.Plugins.Add(agentConversationPlugin);
    }
}
