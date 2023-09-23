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
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Document;
using Microsoft.SemanticKernel.Plugins.Document.FileSystem;
using Microsoft.SemanticKernel.Plugins.Document.OpenXml;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;
using Microsoft.SemanticKernel.Plugins.Web;
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

    internal static ISKFunction GetFunction(this IReadOnlyFunctionCollection skills, string skillName, string functionName)
    {
        return skills.GetFunction(skillName, functionName);
    }

    internal static bool HasSemanticOrNativeFunction(this IReadOnlyFunctionCollection skills, string skillName, string functionName)
    {
        return skills.TryGetFunction(skillName, functionName, out _);
    }

    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The caller invokes native skills during a request and the HttpClient instance must remain alive for those requests to be successful.")]
    internal static void RegisterNativeGraphPlugins(this IKernel kernel, string graphToken, IEnumerable<string>? skillsToLoad = null)
    {
        IList<DelegatingHandler> handlers = GraphClientFactory.CreateDefaultHandlers(new TokenAuthenticationProvider(graphToken));
        GraphServiceClient graphServiceClient = new(GraphClientFactory.Create(handlers));

        if (ShouldLoad(nameof(CloudDrivePlugin), skillsToLoad))
        {
            CloudDrivePlugin cloudDrivePlugin = new(new OneDriveConnector(graphServiceClient));
            _ = kernel.ImportPlugin(cloudDrivePlugin, nameof(cloudDrivePlugin));
        }

        if (ShouldLoad(nameof(TaskListPlugin), skillsToLoad))
        {
            TaskListPlugin taskListPlugin = new(new MicrosoftToDoConnector(graphServiceClient));
            _ = kernel.ImportPlugin(taskListPlugin, nameof(taskListPlugin));
        }

        if (ShouldLoad(nameof(EmailPlugin), skillsToLoad))
        {
            EmailPlugin emailPlugin = new(new OutlookMailConnector(graphServiceClient));
            _ = kernel.ImportPlugin(emailPlugin, nameof(emailPlugin));
        }

        if (ShouldLoad(nameof(CalendarPlugin), skillsToLoad))
        {
            CalendarPlugin calendarPlugin = new(new OutlookCalendarConnector(graphServiceClient));
            _ = kernel.ImportPlugin(calendarPlugin, nameof(calendarPlugin));
        }
    }

    internal static void RegisterTextMemory(this IKernel kernel)
    {
        _ = kernel.ImportPlugin(new TextMemoryPlugin(kernel.Memory), nameof(TextMemoryPlugin));
    }

    internal static void RegisterNativePlugins(this IKernel kernel, IEnumerable<string>? skillsToLoad = null)
    {
        if (ShouldLoad(nameof(DocumentPlugin), skillsToLoad))
        {
            DocumentPlugin documentPlugin = new(new WordDocumentConnector(), new LocalFileSystemConnector());
            _ = kernel.ImportPlugin(documentPlugin, nameof(DocumentPlugin));
        }

        if (ShouldLoad(nameof(ConversationSummaryPlugin), skillsToLoad))
        {
            ConversationSummaryPlugin conversationSummaryPlugin = new(kernel);
            _ = kernel.ImportPlugin(conversationSummaryPlugin, nameof(ConversationSummaryPlugin));
        }

        if (ShouldLoad(nameof(WebFileDownloadPlugin), skillsToLoad))
        {
            var webFileDownloadPlugin = new WebFileDownloadPlugin();
            _ = kernel.ImportPlugin(webFileDownloadPlugin, nameof(WebFileDownloadPlugin));
        }

        if (ShouldLoad(nameof(GitHubPlugin), skillsToLoad))
        {
            GitHubPlugin githubPlugin = new(kernel);
            _ = kernel.ImportPlugin(githubPlugin, nameof(GitHubPlugin));
        }
    }

    internal static void RegisterSemanticFunctions(
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
                    kernel.ImportSemanticPluginFromDirectory(skillsFolder, currentFolder.Name);
                }
                catch (Exception e)
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
