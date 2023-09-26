// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Orchestration;

using Newtonsoft.Json;
using RepoUtils;

/// <summary>
/// This sample shows how to connect the Semantic Kernel to Jira as an Open Api plugin based on the Open Api schema.
/// This format of registering the plugin and its operations, and subsequently executing those operations can be applied
/// to an Open Api plugin that follows the Open Api Schema.
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example24_OpenApiPlugin_Jira
{
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();
        var contextVariables = new ContextVariables();

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";
        contextVariables.Set("server-url", serverUrl);

        IDictionary<string, ISKFunction> jiraFunctions;
        var tokenProvider = new BasicAuthenticationProvider(() =>
        {
            string s = $"{TestConfiguration.Jira.Email}:{TestConfiguration.Jira.ApiKey}";
            return Task.FromResult(s);
        });

        using HttpClient httpClient = new();

        // The bool useLocalFile can be used to toggle the ingestion method for the openapi schema between a file path and a URL
        bool useLocalFile = true;
        if (useLocalFile)
        {
            var apiPluginFile = "./../../../Plugins/JiraPlugin/openapi.json";
            jiraFunctions = await kernel.ImportAIPluginAsync("jiraPlugin", apiPluginFile, new OpenApiFunctionExecutionParameters(authCallback: tokenProvider.AuthenticateRequestAsync));
        }
        else
        {
            var apiPluginRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraFunctions = await kernel.ImportAIPluginAsync("jiraPlugin", apiPluginRawFileURL, new OpenApiFunctionExecutionParameters(httpClient, tokenProvider.AuthenticateRequestAsync));
        }

        // GetIssue Function
        {
            // Set Properties for the Get Issue operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-2");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["GetIssue"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("GetIssue jiraPlugin response: \n{0}", formattedContent);
        }

        // AddComment Function
        {
            // Set Properties for the AddComment operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-1");
            contextVariables.Set("body", "Here is a rad comment");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["AddComment"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("AddComment jiraPlugin response: \n{0}", formattedContent);
        }
    }
}
