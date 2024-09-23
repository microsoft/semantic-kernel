// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base class for agents utilizing <see cref="Microsoft.SemanticKernel.Kernel"/> plugins or services.
/// </summary>
public abstract class KernelAgent : Agent
{
    /// <summary>
    /// Arguments for the agent instruction parameters (optional).
    /// </summary>
    /// <remarks>
    /// Also includes <see cref="PromptExecutionSettings"/>.
    /// </remarks>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// The instructions for the agent (optional)
    /// </summary>
    /// <remarks>
    /// Instructions may be formatted in "semantic-kernel" template format.
    /// (<see cref="KernelPromptTemplateFactory"/>)
    /// </remarks>
    public string? Instructions { get; init; }

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and filters for use throughout the agent lifetime.
    /// </summary>
    /// <remarks>
    /// Defaults to empty Kernel, but may be overridden.
    /// </remarks>
    public Kernel Kernel { get; init; } = new();

    /// <summary>
    /// A prompt-template based on the agent instructions.
    /// </summary>
    protected IPromptTemplate? Template { get; set; }

    /// <summary>
    /// Format the system instructions for the agent.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The formatted system instructions for the agent</returns>
    protected async Task<string?> FormatInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        // If <see cref="Template"/> is not set, default instructions may be treated as "semantic-kernel" template.
        if (this.Template == null)
        {
            if (string.IsNullOrWhiteSpace(this.Instructions))
            {
                return null;
            }

            KernelPromptTemplateFactory templateFactory = new(this.LoggerFactory);
            this.Template = templateFactory.Create(new PromptTemplateConfig(this.Instructions!));
        }

        return await this.Template.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
    }
}
