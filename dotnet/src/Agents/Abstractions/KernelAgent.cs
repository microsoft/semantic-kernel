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
    /// Arguments for the agent instruction paramters (optional).
    /// </summary>
    /// <remarks>
    /// Also includes <see cref="PromptExecutionSettings"/>.
    /// </remarks>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// The instructions for the agent (optional)
    /// </summary>
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
    /// %%% COMMENT
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="arguments"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    protected async Task<string?> FormatInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        if (this.Template == null && !string.IsNullOrWhiteSpace(this.Instructions))
        {
            KernelPromptTemplateFactory templateFactory = new(this.LoggerFactory); // %%% DEFAULT FACTORY ???
            if (templateFactory.TryCreate(new PromptTemplateConfig(this.Instructions!), out IPromptTemplate? template))
            {
                this.Template = template;
            }
        }

        return
            this.Template == null ?
                this.Instructions :
                await this.Template.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
    }
}
