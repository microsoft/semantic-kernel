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
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="instructions">The agent instructions</param>
    /// <param name="arguments">Context arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rendered instructions</returns>
    public static async Task<string> FormatInstructionsAsync(Kernel kernel, string instructions, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        if (arguments != null)
        {
            if (!s_templates.TryGetValue(instructions, out IPromptTemplate template))
            {
                template =
                    s_factory.Create(
                        new PromptTemplateConfig
                        {
                            Template = instructions
                        });

                // Discard local instance if already present
                s_templates.TryAdd(instructions, template);
            }

            instructions = await template.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        }

        return instructions;
    }
}
