// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Document;
using Microsoft.SemanticKernel.Skills.Document.FileSystem;
using Microsoft.SemanticKernel.Skills.Document.OpenXml;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernelFunction.Config;
using Directory = System.IO.Directory;

namespace SemanticKernelFunction;

internal static class Extensions
{
    internal static async Task<HttpResponseData> CreateResponseWithMessageAsync(this HttpRequestData req, HttpStatusCode statusCode, string message)
    {
        HttpResponseData response = req.CreateResponse(statusCode);
        await response.WriteStringAsync(message);
        return response;
    }

    internal static ISKFunction GetFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.HasNativeFunction(skillName, functionName)
            ? skills.GetNativeFunction(skillName, functionName)
            : skills.GetSemanticFunction(skillName, functionName);
    }

    internal static bool HasSemanticOrNativeFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.HasSemanticFunction(skillName, functionName) || skills.HasNativeFunction(skillName, functionName);
    }

    private static bool _ShouldLoad(string skillName, IEnumerable<string>? skillsToLoad = null)
    {
        return skillsToLoad?.Contains(skillName, StringComparer.InvariantCultureIgnoreCase) != false;
    }

    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The caller invokes native skills during a request and the HttpClient instance must remain alive for those requests to be successful.")]
    internal static void RegisterNativeGraphSkills(this IKernel kernel, string graphToken, IEnumerable<string>? skillsToLoad = null)
    {
        IList<DelegatingHandler> handlers = GraphClientFactory.CreateDefaultHandlers(new TokenAuthenticationProvider(graphToken));
        GraphServiceClient graphServiceClient = new(GraphClientFactory.Create(handlers));

        if (_ShouldLoad(nameof(CloudDriveSkill), skillsToLoad))
        {
            CloudDriveSkill cloudDriveSkill = new(new OneDriveConnector(graphServiceClient));
            _ = kernel.ImportSkill(cloudDriveSkill, nameof(cloudDriveSkill));
        }

        if (_ShouldLoad(nameof(TaskListSkill), skillsToLoad))
        {
            TaskListSkill taskListSkill = new(new MicrosoftToDoConnector(graphServiceClient));
            _ = kernel.ImportSkill(taskListSkill, nameof(taskListSkill));
        }

        if (_ShouldLoad(nameof(EmailSkill), skillsToLoad))
        {
            EmailSkill emailSkill = new(new OutlookMailConnector(graphServiceClient));
            _ = kernel.ImportSkill(emailSkill, nameof(emailSkill));
        }

        if (_ShouldLoad(nameof(CalendarSkill), skillsToLoad))
        {
            CalendarSkill calendarSkill = new(new OutlookCalendarConnector(graphServiceClient));
            _ = kernel.ImportSkill(calendarSkill, nameof(calendarSkill));
        }
    }

    internal static void RegisterPlanner(this IKernel kernel)
    {
        PlannerSkill planner = new(kernel);
        _ = kernel.ImportSkill(planner, nameof(PlannerSkill));
    }

    internal static void RegisterNativeSkills(this IKernel kernel, IEnumerable<string>? skillsToLoad = null)
    {
        if (_ShouldLoad(nameof(DocumentSkill), skillsToLoad))
        {
            DocumentSkill documentSkill = new(new WordDocumentConnector(), new LocalFileSystemConnector());
            _ = kernel.ImportSkill(documentSkill, nameof(DocumentSkill));
        }

        if (_ShouldLoad(nameof(ConversationSummarySkill), skillsToLoad))
        {
            ConversationSummarySkill conversationSummarySkill = new(kernel);
            _ = kernel.ImportSkill(conversationSummarySkill, nameof(ConversationSummarySkill));
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

            if (_ShouldLoad(currentFolder.Name, skillsToLoad))
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

    internal static void ConfigureCompletionBackend(this IKernel kernel, ApiKeyConfig apiConfig)
    {
        // The Semantic Kernel supports both Azure OpenAI and OpenAI completion backends (and both can exist concurrently)
        // Each Skill can determine which model it needs which via internal orchestration, the kernel will delegate to the appropriate backend

        switch (apiConfig.CompletionBackend)
        {
            case CompletionService.AzureOpenAI:
                _ = kernel.Config.AddAzureOpenAICompletionBackend(
                    apiConfig.Label,
                    apiConfig.DeploymentOrModelId,
                    apiConfig.Endpoint,
                    apiConfig.Key);

                break;
            case CompletionService.OpenAI:
                _ = kernel.Config.AddOpenAICompletionBackend(
                    apiConfig.Label,
                    apiConfig.DeploymentOrModelId,
                    apiConfig.Key);

                break;
            default:
                break;
        }
    }
}
