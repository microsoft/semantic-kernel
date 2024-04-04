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
    /// <param name="instructions">The instructions to format.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rendered instructions</returns>
    public static async Task<string?> FormatInstructionsAsync(KernelAgent agent, string? instructions, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(instructions))
        {
            return null;
        }

        if (agent.InstructionArguments != null)
        {
            if (!s_templates.TryGetValue(agent.Id, out TemplateReference templateReference) ||
                !templateReference.IsConsistent(instructions!))
            {
                // Generate and cache prompt template if does not exist or if instructions have changed.
                IPromptTemplate template =
                    s_factory.Create(
                        new PromptTemplateConfig
                        {
                            Template = instructions!
                        });

                templateReference = new(template, instructions!);
                s_templates[agent.Id] = templateReference;
            }

            instructions = await templateReference.Template.RenderAsync(agent.Kernel, agent.InstructionArguments, cancellationToken).ConfigureAwait(false);
        }

        return instructions;
    }

    /// <summary>
    /// Tracks template with ability to verify instruction consistency.
    /// </summary>
    private class TemplateReference
    {
        private readonly int _instructionHash;

        public IPromptTemplate Template { get; }

        public bool IsConsistent(string instructions)
        {
            return this._instructionHash == instructions.GetHashCode();
        }

        public TemplateReference(IPromptTemplate template, string instructions)
        {
            this.Template = template;
            this._instructionHash = instructions.GetHashCode();
        }
    }
}
