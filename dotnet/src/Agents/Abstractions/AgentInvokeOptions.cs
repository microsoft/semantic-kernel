// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Optional parameters for agent invocation.
/// </summary>
public class AgentInvokeOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentInvokeOptions"/> class.
    /// </summary>
    public AgentInvokeOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public AgentInvokeOptions(AgentInvokeOptions options)
    {
        Verify.NotNull(options);

        this.KernelArguments = options.KernelArguments;
        this.Kernel = options.Kernel;
        this.AdditionalInstructions = options.AdditionalInstructions;
    }

    /// <summary>
    /// Gets or sets optional arguments to pass to the agent's invocation, including any <see cref="PromptExecutionSettings"/>
    /// </summary>
    public KernelArguments? KernelArguments { get; init; } = null;

    /// <summary>
    /// Gets or sets the <see cref="Kernel"/> containing services, plugins, and other state for use by the agent
    /// </summary>
    public Kernel? Kernel { get; init; } = null;

    /// <summary>
    /// Gets or sets any instructions, in addition to those that were provided to the agent
    /// initially, that need to be added to the prompt for this invocation only.
    /// </summary>
    public string AdditionalInstructions { get; init; } = string.Empty;
}
