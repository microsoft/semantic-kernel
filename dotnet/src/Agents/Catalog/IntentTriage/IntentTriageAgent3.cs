// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
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
public sealed partial class IntentTriageAgent3 : ComposedServiceAgent
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
                Instructions = this.GetInstructions(),
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

        string apispec = await this.BindSpecAsync(
            resourceStream,
            new()
            {
                { "language.resourceUrl", this._settings.ApiEndpoint},
                { "language.resourceConnectionName", "xyz"},
                { "language.resourceVersion", this._settings.ApiVersion},
            },
            cancellationToken);

        await using Stream streamSpec = ToStream(apispec);

        HttpClient client = new();
        client.DefaultRequestHeaders.Add(LanguagePlugin.HeaderSubscriptionKey, this._settings.ApiKey);

        KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            Names.CognitiveLanguagePlugin,
            streamSpec,
            new OpenApiFunctionExecutionParameters
            {
                IgnoreNonCompliantErrors = true,
                EnableDynamicPayload = false,
                HttpClient = client,
            },
            cancellationToken).ConfigureAwait(false);

        return plugin;
    }

    private async ValueTask<KernelPlugin> DefineQuestionAndAnswerToolsAsync(CancellationToken cancellationToken)
    {
        await using Stream resourceStream = AgentResources.OpenStream(Resources.QuestionAndAnswer, Assembly.GetExecutingAssembly());

        string apispec = await this.BindSpecAsync(
            resourceStream,
            new()
            {
                { "language.resourceUrl", this._settings.ApiEndpoint},
                { "language.resourceConnectionName", "xyz"},
                { "language.resourceVersion", this._settings.ApiVersion},
                { "cqa.projectName", this._settings.QueryProject},
                { "cqa.deploymentName", this._settings.QueryDeployment},
            },
            cancellationToken);

        await using Stream streamSpec = ToStream(apispec);

        HttpClient client = new();
        client.DefaultRequestHeaders.Add(LanguagePlugin.HeaderSubscriptionKey, this._settings.ApiKey);

        KernelPlugin plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync(
            Names.QuestionAndAnswerPlugin,
            streamSpec,
            new OpenApiFunctionExecutionParameters
            {
                IgnoreNonCompliantErrors = true,
                EnableDynamicPayload = false,
                HttpClient = client,
            },
            cancellationToken).ConfigureAwait(false);

        return plugin;
    }

    private async ValueTask<string> BindSpecAsync(Stream resourceStream, Dictionary<string, string> parameters, CancellationToken cancellationToken)
    {
        using StreamReader reader = new(resourceStream);
        string apispec = await reader.ReadToEndAsync(cancellationToken);

        return SpecParameterBindingExpression().Replace(
            apispec,
            match =>
            {
                string key = match.Groups[1].Value;
                return parameters.TryGetValue(key, out string? value) ? value : match.Value;
            });
    }

    private static MemoryStream ToStream(string input)
    {
        byte[] byteArray = Encoding.UTF8.GetBytes(input);
        return new MemoryStream(byteArray);
    }

    [GeneratedRegex(@"\$\{([^}]+)\}")]
    private static partial Regex SpecParameterBindingExpression();

    private string GetInstructions() =>
        $$$"""
        You are a triage agent. Your goal is to answer questions and redirect message according to their intent. You have at your disposition 2 tools: 
         1. cqa_api: to answer customer questions such as procedures and FAQs
         2. clu_api: to extract the intent of the message. 
        You must use the tools to perform your task. Only if the tools are not able to provide information you can answer according to your general knowledge. 
          - When you return answers from the cqa_api return the exact answer without rewriting the answer. 
          - When you return answers from the clu_api return 'Detected Intent: {intent response}' and fill {intent response} with the intent returned from the api. 
        To call the clu_api, the following parameters values should be used in the payload: 
          - 'projectName': value must be '${{{this._settings.AnalyzeProject}}}' 
          - 'deploymentName': value must be '${{{this._settings.AnalyzeDeployment}}}'
          - 'text': must be the input from the user.
        """;
}
