// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Newtonsoft.Json;
using RepoUtils;

/// <summary>
/// This sample shows how to connect the Semantic Kernel to Jira as an Open Api plugin based on the Open Api schema.
/// This format of registering the skill and its operations, and subsequently executing those operations can be applied
/// to an Open Api plugin that follows the Open Api Schema.
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example24_OpenApiSkill_Jira
{
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().AddLogging(ConsoleLogger.Log).Build();
        var contextVariables = new ContextVariables();

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";
        contextVariables.Set("server-url", serverUrl);

        IDictionary<string, ISKFunction> jiraSkills;
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
            var apiSkillFile = "./../../../Skills/JiraSkill/openapi.json";
            jiraSkills = await kernel.ImportOpenApiSkillFromFileAsync("jiraSkills", apiSkillFile, new OpenApiSkillExecutionParameters(authCallback: tokenProvider.AuthenticateRequestAsync));
        }
        else
        {
            var apiSkillRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraSkills = await kernel.ImportOpenApiSkillFromUrlAsync("jiraSkills", apiSkillRawFileURL, new OpenApiSkillExecutionParameters(httpClient, tokenProvider.AuthenticateRequestAsync));
        }

        // GetIssue Skill
        {
            // Set Properties for the Get Issue operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-2");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraSkills["GetIssue"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.Result), Formatting.Indented);
            Console.WriteLine("GetIssue jiraSkills response: \n{0}", formattedContent);
        }

        // AddComment Skill
        {
            // Set Properties for the AddComment operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-1");
            contextVariables.Set("body", "Here is a rad comment");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraSkills["AddComment"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.Result), Formatting.Indented);
            Console.WriteLine("AddComment jiraSkills response: \n{0}", formattedContent);
        }
    }
}
