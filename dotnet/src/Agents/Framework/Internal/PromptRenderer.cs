// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Utility class for rendering an agent's system instructions.
/// </summary>
internal static class PromptRenderer
{
    private static readonly KernelPromptTemplateFactory s_factory = new();
    private static readonly ConcurrentDictionary<string, TemplateReference> s_templates = new();

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
            if (!s_templates.TryGetValue(agent.Id, out TemplateReference templateReference) ||
                !templateReference.IsConsistent(agent.Instructions))
            {
                // Generate and cache prompt template if does not exist or if instructions have changed.
                IPromptTemplate template =
                    s_factory.Create(
                        new PromptTemplateConfig
                        {
                            Template = agent.Instructions!
                        });

                templateReference = new(template, instructions);
                s_templates[agent.Id] = templateReference;
            }

            instructions = await templateReference.Template.RenderAsync(agent.Kernel, agent.InstructionArguments, cancellationToken).ConfigureAwait(false);
        }

        return instructions ?? agent.Instructions;
    }

    /// <summary>
    /// Tracks template with ability to verify instruction consistency.
    /// </summary>
    private readonly struct TemplateReference
    {
        private readonly int _instructionHash;

        public IPromptTemplate Template { get; }

        public bool IsConsistent(string? instructions)
        {
            return this._instructionHash == (instructions?.GetHashCode() ?? 0);
        }

        public TemplateReference(IPromptTemplate template, string? instructions)
        {
            this.Template = template;
            this._instructionHash = instructions?.GetHashCode() ?? 0;
        }
    }
}
