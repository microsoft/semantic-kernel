// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.IntentTriage.Internal;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

internal static class LanguageApiSpec
{
    private static class Resources
    {
        public const string CognitiveLanguage = "ToolResources.clu.json";
        public const string QuestionAndAnswer = "ToolResources.cqa.json";
    }

    private static class TemplateParameters
    {
        public const string ServiceUrl = "language.resourceUrl";
        public const string ServiceConnection = "language.resourceConnectionName";
        public const string ServiceVersion = "language.resourceVersion";
        public const string AnalyzeProject = "clu.projectName";
        public const string AnalyzeDeployment = "clu.deploymentName";
        public const string QueryProject = "cqa.projectName";
        public const string QueryDeployment = "cqa.deploymentName";
    }

    public static async Task<string> LoadCLUSpecAsync(IntentTriageLanguageSettings settings, CancellationToken cancellationToken = default)
    {
        await using Stream resourceStream = AgentResources.OpenStream(Resources.CognitiveLanguage, Assembly.GetExecutingAssembly());

        string apispec = await resourceStream.BindParametersAsync(
            new()
            {
                { TemplateParameters.ServiceUrl, settings.ApiEndpoint},
                { TemplateParameters.ServiceVersion, settings.ApiVersion},
                { TemplateParameters.ServiceConnection, "none"},
            },
            cancellationToken);

        return apispec;
    }

    public static async Task<string> LoadCQASpecAsync(IntentTriageLanguageSettings settings, CancellationToken cancellationToken = default)
    {
        await using Stream resourceStream = AgentResources.OpenStream(Resources.QuestionAndAnswer, Assembly.GetExecutingAssembly());

        string apispec = await resourceStream.BindParametersAsync(
            new()
            {
                { TemplateParameters.ServiceUrl, settings.ApiEndpoint},
                { TemplateParameters.ServiceVersion, settings.ApiVersion},
                { TemplateParameters.ServiceConnection, "none"},
                { TemplateParameters.QueryProject, settings.QueryProject},
                { TemplateParameters.QueryDeployment, settings.QueryDeployment},
            },
            cancellationToken);

        return apispec;
    }
}
