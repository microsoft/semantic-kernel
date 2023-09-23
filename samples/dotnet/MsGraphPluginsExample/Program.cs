// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Client;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using DayOfWeek = System.DayOfWeek;

namespace MsGraphPluginsExample;

/// <summary>
/// The static plan below is meant to emulate a plan generated from the following request:
///   "Summarize the content of cheese.txt and send me an email with the summary and a link to the file.
///    Then add a reminder to follow-up next week."
/// </summary>
public sealed class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        #region Initialization

        // Load configuration
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "appsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "appsettings.Development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Program>()
            .Build();

        // Initialize logger
        using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
        {
            builder.AddConfiguration(configuration.GetSection("Logging"))
                .AddConsole()
                .AddDebug();
        });

        ILogger logger = loggerFactory.CreateLogger<Program>();

        MsGraphConfiguration? candidateGraphApiConfig = configuration.GetRequiredSection("MsGraph").Get<MsGraphConfiguration>()
                                                        ?? throw new InvalidOperationException("Missing configuration for Microsoft Graph API.");

        // Workaround for nested types not working IConfigurationSection.Get<T>()
        // See https://github.com/dotnet/runtime/issues/77677
        configuration.GetSection("MsGraph:Scopes").Bind(candidateGraphApiConfig.Scopes);
        if (candidateGraphApiConfig.Scopes == null)
        {
            throw new InvalidOperationException("Missing Scopes configuration for Microsoft Graph API.");
        }

        MsGraphConfiguration graphApiConfiguration = candidateGraphApiConfig;

        string? defaultCompletionServiceId = configuration["DefaultCompletionServiceId"];
        if (string.IsNullOrWhiteSpace(defaultCompletionServiceId))
        {
            throw new InvalidOperationException("'DefaultCompletionServiceId' is not set in configuration.");
        }

        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        #endregion

        // Initialize the Graph API client with interactive authentication and local caching.
        // Note that LocalUserMSALCredentialManager is NOT safe for multi-user and cloud-service deployments.
        // TODO: Include sample code credential manager for multi-user and cloud service scenario.
        // TODO: the var is never used
        LocalUserMSALCredentialManager credentialManager = await LocalUserMSALCredentialManager.CreateAsync();

        // For more details on creating a Graph API client and choosing authentication provider see:
        //   https://learn.microsoft.com/graph/sdks/create-client
        //   https://learn.microsoft.com/graph/sdks/choose-authentication-providers

        // Add authentication handler.
        IList<DelegatingHandler> handlers = GraphClientFactory.CreateDefaultHandlers(
            CreateAuthenticationProvider(await LocalUserMSALCredentialManager.CreateAsync(), graphApiConfiguration));

        // Add logging handler to log Graph API requests and responses request IDs.
        using MsGraphClientLoggingHandler loggingHandler = new(logger);
        handlers.Add(loggingHandler);

        // Create the Graph client.
        using HttpClient httpClient = GraphClientFactory.Create(handlers);
        GraphServiceClient graphServiceClient = new(httpClient);

        // Initialize SK Graph API Plugins we'll be using in the plan.
        CloudDrivePlugin oneDrivePlugin = new(new OneDriveConnector(graphServiceClient), loggerFactory);
        TaskListPlugin todoPlugin = new(new MicrosoftToDoConnector(graphServiceClient), loggerFactory);
        EmailPlugin outlookPlugin = new(new OutlookMailConnector(graphServiceClient), loggerFactory);

        // Initialize the Semantic Kernel and and register connections with OpenAI/Azure OpenAI instances.
        KernelBuilder builder = Kernel.Builder.WithLoggerFactory(loggerFactory);

        if (configuration.GetSection("AzureOpenAI:ServiceId").Value != null)
        {
            AzureOpenAIConfiguration? azureOpenAIConfiguration = configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
            if (azureOpenAIConfiguration != null)
            {
                builder.WithAzureChatCompletionService(
                        deploymentName: azureOpenAIConfiguration.DeploymentName,
                        endpoint: azureOpenAIConfiguration.Endpoint,
                        apiKey: azureOpenAIConfiguration.ApiKey,
                        serviceId: azureOpenAIConfiguration.ServiceId,
                        setAsDefault: azureOpenAIConfiguration.ServiceId == defaultCompletionServiceId);
            }
        }

        if (configuration.GetSection("OpenAI:ServiceId").Value != null)
        {
            OpenAIConfiguration? openAIConfiguration = configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
            if (openAIConfiguration != null)
            {
                builder.WithOpenAIChatCompletionService(
                    modelId: openAIConfiguration.ModelId,
                    apiKey: openAIConfiguration.ApiKey,
                    serviceId: openAIConfiguration.ServiceId,
                    setAsDefault: openAIConfiguration.ServiceId == defaultCompletionServiceId);
            }
        }

        IKernel sk = builder.Build();

        var onedriveFunctions = sk.ImportPlugin(oneDrivePlugin, "onedrive");
        var todoFunctions = sk.ImportPlugin(todoPlugin, "todo");
        var outlookFunctions = sk.ImportPlugin(outlookPlugin, "outlook");

        string skillParentDirectory = RepoFiles.SamplePluginsPath();

        IDictionary<string, ISKFunction> summarizeFunctions =
            sk.ImportSemanticPluginFromDirectory(skillParentDirectory, "SummarizePlugin");

        //
        // The static plan below is meant to emulate a plan generated from the following request:
        // "Summarize the content of cheese.txt and send me an email with the summary and a link to the file. Then add a reminder to follow-up next week."
        //
        string? pathToFile = configuration["OneDrivePathToFile"];
        if (string.IsNullOrWhiteSpace(pathToFile))
        {
            throw new InvalidOperationException("OneDrivePathToFile is not set in configuration.");
        }

        // Get file content
        KernelResult fileContentResult = await sk.RunAsync(pathToFile,
            onedriveFunctions["GetFileContent"],
            summarizeFunctions["Summarize"]);
        string? fileSummary = fileContentResult.GetValue<string>();

        // Get my email address
        KernelResult emailAddressResult = await sk.RunAsync(string.Empty, outlookFunctions["GetMyEmailAddress"]);
        string? myEmailAddress = emailAddressResult.GetValue<string>();

        // Create a link to the file
        KernelResult fileLinkResult = await sk.RunAsync(pathToFile, onedriveFunctions["CreateLink"]);
        string? fileLink = fileLinkResult.GetValue<string>();

        // Send me an email with the summary and a link to the file.
        ContextVariables emailMemory = new($"{fileSummary}{Environment.NewLine}{Environment.NewLine}{fileLink}");
        emailMemory.Set(EmailPlugin.Parameters.Recipients, myEmailAddress);
        emailMemory.Set(EmailPlugin.Parameters.Subject, $"Summary of {pathToFile}");

        await sk.RunAsync(emailMemory, outlookFunctions["SendEmail"]);

        // Add a reminder to follow-up next week.
        ContextVariables followUpTaskMemory = new($"Follow-up about {pathToFile}.");
        DateTimeOffset nextMonday = TaskListPlugin.GetNextDayOfWeek(DayOfWeek.Monday, TimeSpan.FromHours(9));
        followUpTaskMemory.Set(TaskListPlugin.Parameters.Reminder, nextMonday.ToString("o"));
        await sk.RunAsync(followUpTaskMemory, todoFunctions["AddTask"]);

        logger.LogInformation("Done!");
    }

    /// <summary>
    /// Create a delegated authentication callback for the Graph API client.
    /// </summary>
    private static DelegateAuthenticationProvider CreateAuthenticationProvider(
        LocalUserMSALCredentialManager credentialManager,
        MsGraphConfiguration config)
        => new(
            async (requestMessage) =>
            {
                requestMessage.Headers.Authorization = new AuthenticationHeaderValue(
                    scheme: "bearer",
                    parameter: await credentialManager.GetTokenAsync(
                        config.ClientId,
                        config.TenantId,
                        config.Scopes.ToArray(),
                        config.RedirectUri));
            });
}
