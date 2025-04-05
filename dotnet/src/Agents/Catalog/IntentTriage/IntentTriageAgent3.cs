// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// An example <see cref="ServiceAgent"/> based on chat-completion API.
/// </summary>
/// <remarks>
/// This agent configures the language services as tools for the LLM
/// to invoke and the LLM drives response generation. (Typical approach)
/// </remarks>
[ServiceAgentProvider<IntentTriageAgentProvider2>]
public sealed class IntentTriageAgent3 : ComposedServiceAgent
{
    private static class Names
    {
        public const string CognitiveLanguagePlugin = nameof(CognitiveLanguagePlugin);
        public const string QuestionAndAnswerPlugin = nameof(QuestionAndAnswerPlugin);
    }

    private static class Resources
    {
        public const string CognitiveLanguage = "ToolResources.clu.json";
        public const string QuestionAndAnswer = "ToolResources.cqa.json";
    }

    private readonly IntentTriageLanguageSettings _settings;

    /// <summary>
    /// Initializes a new instance of the <see cref="IntentTriageAgent1"/> class.
    /// </summary>
    /// <param name="settings">Settings for usinge the language services.</param>
    public IntentTriageAgent3(IntentTriageLanguageSettings settings)
    {
        this._settings = settings;
    }

    /// <inheritdoc/>
    protected override async Task<Agent> CreateAgentAsync(CancellationToken cancellationToken)
    {
        this.Kernel.Plugins.Add(await this.DefineCognitiveLanguageToolsAsync(cancellationToken));
        this.Kernel.Plugins.Add(await this.DefineQuestionAndAnswerToolsAsync(cancellationToken));

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

        return agent;
    }

    internal async ValueTask<KernelPlugin> DefineCognitiveLanguageToolsAsync(CancellationToken cancellationToken)
    {
        await using Stream resourceStream = AgentResources.OpenStream(Resources.CognitiveLanguage, Assembly.GetExecutingAssembly());

        // %%% TODO: PARAMETERS
        KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            Names.CognitiveLanguagePlugin,
            resourceStream,
            new OpenApiFunctionExecutionParameters
            {
                IgnoreNonCompliantErrors = true,
                EnableDynamicPayload = false,
            },
            cancellationToken).ConfigureAwait(false);

        return plugin;
    }

    private async ValueTask<KernelPlugin> DefineQuestionAndAnswerToolsAsync(CancellationToken cancellationToken)
    {
        await using Stream resourceStream = AgentResources.OpenStream(Resources.QuestionAndAnswer, Assembly.GetExecutingAssembly());

        // %%% TODO: PARAMETERS
        KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            Names.QuestionAndAnswerPlugin,
            resourceStream,
            new OpenApiFunctionExecutionParameters
            {
                IgnoreNonCompliantErrors = true,
                EnableDynamicPayload = false,
            },
            cancellationToken).ConfigureAwait(false);

        return plugin;
    }
}
