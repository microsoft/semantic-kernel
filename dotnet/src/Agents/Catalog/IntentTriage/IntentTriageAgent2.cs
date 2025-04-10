// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// An example <see cref="ComposedServiceAgent"/> based on an
/// inner <see cref="ChatCompletionAgent"/> that relies on two
/// language service  API's as tooling.  The invocation of the
/// language service API's are performed within a <see cref="KernelPlugin"/>.
/// </summary>s
/// <remarks>
/// This agent configures the language service API's as tools for the LLM
/// to invoke and as part of the model's tool calling protocol.
/// (Typical approach)
/// </remarks>
[ServiceAgentProvider<IntentTriageAgentProvider2>]
public sealed class IntentTriageAgent2 : ComposedServiceAgent
{
    private readonly IntentTriageLanguageSettings _settings;

    /// <summary>
    /// Initializes a new instance of the <see cref="IntentTriageAgent1"/> class.
    /// </summary>
    /// <param name="settings">Settings for usinge the language services.</param>
    public IntentTriageAgent2(IntentTriageLanguageSettings settings)
    {
        this._settings = settings;
    }

    /// <inheritdoc/>
    protected override Task<Agent> CreateAgentAsync(CancellationToken cancellationToken)
    {
        this.Kernel.Plugins.AddFromObject(new LanguagePlugin(this._settings));

        ChatCompletionAgent agent =
            new()
            {
                Name = this.Name,
                Instructions = IntentTriageAgentDefinition.Instructions,
                Kernel = this.Kernel,
                Arguments =
                    this.Arguments ??
                    new KernelArguments(
                        new PromptExecutionSettings()
                        {
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
                        })
            };

        return Task.FromResult<Agent>(agent);
    }
}
