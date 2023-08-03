// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using KernelHttpServer.Config;
using KernelHttpServer.Plugins;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.Skills.Document;
using Microsoft.SemanticKernel.Skills.Document.FileSystem;
using Microsoft.SemanticKernel.Skills.Document.OpenXml;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.TemplateEngine;
using static KernelHttpServer.Config.Constants;
using Directory = System.IO.Directory;

namespace KernelHttpServer;

internal static class Extensions
{
    internal static ApiKeyConfig ToApiKeyConfig(this HttpRequestData req)
    {
        var apiConfig = new ApiKeyConfig();

        // completion values
        if (req.Headers.TryGetValues(SKHttpHeaders.CompletionService, out var completionAIService))
        {
            apiConfig.CompletionConfig.AIService = Enum.Parse<AIService>(completionAIService.First());
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.CompletionModel, out var completionModelValue))
        {
            apiConfig.CompletionConfig.DeploymentOrModelId = completionModelValue.First();
            apiConfig.CompletionConfig.ServiceId = apiConfig.CompletionConfig.DeploymentOrModelId;
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.CompletionEndpoint, out var completionEndpoint))
        {
            apiConfig.CompletionConfig.Endpoint = completionEndpoint.First();
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.CompletionKey, out var completionKey))
        {
            apiConfig.CompletionConfig.Key = completionKey.First();
        }

        // embedding values
        if (req.Headers.TryGetValues(SKHttpHeaders.EmbeddingService, out var embeddingAIService))
        {
            apiConfig.EmbeddingConfig.AIService = Enum.Parse<AIService>(embeddingAIService.First());
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.EmbeddingModel, out var embeddingModelValue))
        {
            apiConfig.EmbeddingConfig.DeploymentOrModelId = embeddingModelValue.First();
            apiConfig.EmbeddingConfig.ServiceId = apiConfig.EmbeddingConfig.DeploymentOrModelId;
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.EmbeddingEndpoint, out var embeddingEndpoint))
        {
            apiConfig.EmbeddingConfig.Endpoint = embeddingEndpoint.First();
        }

        if (req.Headers.TryGetValues(SKHttpHeaders.EmbeddingKey, out var embeddingKey))
        {
            apiConfig.EmbeddingConfig.Key = embeddingKey.First();
        }

        return apiConfig;
    }

    internal static async Task<HttpResponseData> CreateResponseWithMessageAsync(this HttpRequestData req, HttpStatusCode statusCode, string message)
    {
        HttpResponseData response = req.CreateResponse(statusCode);
        await response.WriteStringAsync(message);
        return response;
    }

    internal static ISKFunction GetFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.GetFunction(skillName, functionName);
    }

    internal static bool HasSemanticOrNativeFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.TryGetFunction(skillName, functionName, out _);
    }

    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The caller invokes native skills during a request and the HttpClient instance must remain alive for those requests to be successful.")]
    internal static void RegisterNativeGraphSkills(this IKernel kernel, string graphToken, IEnumerable<string>? skillsToLoad = null)
    {
        IList<DelegatingHandler> handlers = GraphClientFactory.CreateDefaultHandlers(new TokenAuthenticationProvider(graphToken));
        GraphServiceClient graphServiceClient = new(GraphClientFactory.Create(handlers));

        if (ShouldLoad(nameof(CloudDriveSkill), skillsToLoad))
        {
            CloudDriveSkill cloudDriveSkill = new(new OneDriveConnector(graphServiceClient));
            _ = kernel.ImportSkill(cloudDriveSkill, nameof(cloudDriveSkill));
        }

        if (ShouldLoad(nameof(TaskListSkill), skillsToLoad))
        {
            TaskListSkill taskListSkill = new(new MicrosoftToDoConnector(graphServiceClient));
            _ = kernel.ImportSkill(taskListSkill, nameof(taskListSkill));
        }

        if (ShouldLoad(nameof(EmailSkill), skillsToLoad))
        {
            EmailSkill emailSkill = new(new OutlookMailConnector(graphServiceClient));
            _ = kernel.ImportSkill(emailSkill, nameof(emailSkill));
        }

        if (ShouldLoad(nameof(CalendarSkill), skillsToLoad))
        {
            CalendarSkill calendarSkill = new(new OutlookCalendarConnector(graphServiceClient));
            _ = kernel.ImportSkill(calendarSkill, nameof(calendarSkill));
        }
    }

    internal static void RegisterTextMemory(this IKernel kernel)
    {
        _ = kernel.ImportSkill(new TextMemorySkill(kernel.Memory), nameof(TextMemorySkill));
    }

    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The caller invokes native skills during a request and the skill instances must remain alive for those requests to be successful.")]
    internal static void RegisterNativeSkills(this IKernel kernel, IEnumerable<string>? skillsToLoad = null)
    {
        if (ShouldLoad(nameof(DocumentSkill), skillsToLoad))
        {
            DocumentSkill documentSkill = new(new WordDocumentConnector(), new LocalFileSystemConnector());
            _ = kernel.ImportSkill(documentSkill, nameof(DocumentSkill));
        }

        if (ShouldLoad(nameof(ConversationSummarySkill), skillsToLoad))
        {
            ConversationSummarySkill conversationSummarySkill = new(kernel);
            _ = kernel.ImportSkill(conversationSummarySkill, nameof(ConversationSummarySkill));
        }

        if (ShouldLoad(nameof(WebFileDownloadSkill), skillsToLoad))
        {
            var webFileDownloadSkill = new WebFileDownloadSkill();
            _ = kernel.ImportSkill(webFileDownloadSkill, nameof(WebFileDownloadSkill));
        }

        if (ShouldLoad(nameof(GitHubPlugin), skillsToLoad))
        {
            GitHubPlugin githubPlugin = new(kernel);
            _ = kernel.ImportSkill(githubPlugin, nameof(GitHubPlugin));
        }
    }

    internal static void RegisterSemanticSkills(
        this IKernel kernel,
        string skillsFolder,
        ILogger logger,
        IEnumerable<string>? skillsToLoad = null)
    {
        foreach (string skPromptPath in Directory.EnumerateFiles(skillsFolder, "*.txt", SearchOption.AllDirectories))
        {
            FileInfo fInfo = new(skPromptPath);
            DirectoryInfo? currentFolder = fInfo.Directory;

            while (currentFolder?.Parent?.FullName != skillsFolder)
            {
                currentFolder = currentFolder?.Parent;
            }

            if (ShouldLoad(currentFolder.Name, skillsToLoad))
            {
                try
                {
                    _ = kernel.ImportSemanticSkillFromDirectory(skillsFolder, currentFolder.Name);
                }
                catch (TemplateException e)
                {
                    logger.LogWarning("Could not load skill from {0} with error: {1}", currentFolder.Name, e.Message);
                }
            }
        }
    }

    private static bool ShouldLoad(string skillName, IEnumerable<string>? skillsToLoad = null)
    {
        return skillsToLoad?.Contains(skillName, StringComparer.OrdinalIgnoreCase) != false;
    }
}
