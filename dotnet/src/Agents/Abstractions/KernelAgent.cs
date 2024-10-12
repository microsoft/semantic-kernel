// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
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
    public IPromptTemplate? Template { get; protected set; }

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

    /// <summary>
    /// Provide a merged instance of <see cref="KernelArguments"/> with precedence for override arguments.
    /// </summary>
    /// <param name="arguments">The override arguments</param>
    /// <remarks>
    /// This merge preserves original <see cref="PromptExecutionSettings"/> and <see cref="KernelArguments"/> parameters.
    /// and allows for incremental addition or replacement of specific parameters while also preserving the ability
    /// to override the execution settings.
    /// </remarks>
    protected KernelArguments? MergeArguments(KernelArguments? arguments)
    {
        // Avoid merge when default arguments are not set.
        if (this.Arguments == null)
        {
            return arguments;
        }

        // Avoid merge when override arguments are not set.
        if (arguments == null)
        {
            return this.Arguments;
        }

        // Both instances are not null, merge with precedence for override arguments.

        // Merge execution settings with precedence for override arguments.
        Dictionary<string, PromptExecutionSettings>? settings =
            (arguments.ExecutionSettings ?? s_emptySettings)
                .Concat(this.Arguments.ExecutionSettings ?? s_emptySettings)
                .GroupBy(entry => entry.Key)
                .ToDictionary(entry => entry.Key, entry => entry.First().Value);

        // Merge parameters with precedence for override arguments.
        Dictionary<string, object?>? parameters =
            arguments
                .Concat(this.Arguments)
                .GroupBy(entry => entry.Key)
                .ToDictionary(entry => entry.Key, entry => entry.First().Value);

        return new KernelArguments(parameters, settings);
    }

    private static readonly Dictionary<string, PromptExecutionSettings> s_emptySettings = [];
}
