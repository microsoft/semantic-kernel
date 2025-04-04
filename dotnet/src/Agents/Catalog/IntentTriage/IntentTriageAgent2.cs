// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// An example <see cref="ServiceAgent"/> based on chat-completion API.
/// </summary>
/// <remarks>
/// This agent configures the language services as tools for the LLM
/// to invoke and the LLM drives response generation. (Typical approach)
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
    protected override Task<Agent> CreateAgentAsync()
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
