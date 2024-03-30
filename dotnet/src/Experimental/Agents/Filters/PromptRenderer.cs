// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Filters;

internal static class PromptRenderer
{
    private static readonly KernelPromptTemplateFactory s_factory = new();
    private static readonly ConcurrentDictionary<string, IPromptTemplate> s_templates = [];

    /// <summary>
    /// Render the provided instructions using the specified arguments.
    /// </summary>
    /// <param name="agent">A <see cref="KernelAgent"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rendered instructions</returns>
    public static async Task<string?> FormatInstructionsAsync(KernelAgent agent, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(agent.Instructions))
        {
            return null;
        }

        string? instructions = null;

        if (agent.InstructionArguments != null)
        {
            if (!s_templates.TryGetValue(agent.Id, out IPromptTemplate template)) // $$$ INSTRUCTION CONSISTENCY
            {
                template =
                    s_factory.Create(
                        new PromptTemplateConfig
                        {
                            Template = agent.Instructions!
                        });

                // Discard local instance if already present in dictionary
                s_templates.TryAdd(agent.Id, template);
            }

            instructions = await template.RenderAsync(agent.Kernel, agent.InstructionArguments, cancellationToken).ConfigureAwait(false);
        }

        return instructions ?? agent.Instructions;
    }
}
