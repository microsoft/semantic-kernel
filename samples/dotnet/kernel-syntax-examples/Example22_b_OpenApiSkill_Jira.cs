// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RepoUtils;

public static class Example22_b_OpenApiSkill_Jira
{
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        var contextVariables = new ContextVariables();

        string s_serverURL = "https://<jiraProject>.atlassian.net/rest/api/latest/";
        contextVariables.Set("server-url", s_serverURL);

        IDictionary<string, ISKFunction> jiraSkills;
        var tokenProvider = new BasicAuthenticationProvider(AuthenticateWithBasicAPITokenAsync);

        bool bUseLocalFile = true;
        if (bUseLocalFile)
        {
            var apiSkillFile = "./../../../Skills/JiraSkill/openapi.json";
            jiraSkills = await kernel.ImportOpenApiSkillFromFileAsync("jiraSkills", apiSkillFile, tokenProvider.AuthenticateRequestAsync);
        }
        else
        {
            var apiSkillRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraSkills = await kernel.ImportOpenApiSkillFromUrlAsync("jiraSkills", apiSkillRawFileURL, null, tokenProvider.AuthenticateRequestAsync);
        }


        await GetIssueSkillAsync(kernel, jiraSkills, contextVariables);
        await AddCommentSkillAsync(kernel, jiraSkills, contextVariables);
    }

    private static async Task GetIssueSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //Set Properties for the Get Issue operation in the openAPI.swagger.json 
        contextVariables.Set("issueKey", "SKTES-2");

        //Run operation via the semantic kernel
        var result = await kernel.RunAsync(contextVariables, jiraSkills["GetIssue"]);

        Console.WriteLine("\n\n\n");
        var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.Result), Formatting.Indented);
        Console.WriteLine("GetIssue jiraSkills response: \n{0}", formattedContent);
    }

    private static async Task AddCommentSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //Set Properties for the AddComment operation in the openAPI.swagger.json 
        contextVariables.Set("issueKey", "SKTES-1");
        contextVariables.Set("body", "Here is a rad comment");

        //Run operation via the semantic kernel
        var result = await kernel.RunAsync(contextVariables, jiraSkills["AddComment"]);

        Console.WriteLine("\n\n\n");
        var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.Result), Formatting.Indented);
        Console.WriteLine("AddComment jiraSkills response: \n{0}", formattedContent);
    }

    private static Task<string> AuthenticateWithBasicAPITokenAsync()
    {
        string s = Env.Var("MY_EMAIL_ADDRESS") + ":" + Env.Var("JIRA_API_KEY");
        return Task.FromResult(s);
    }
}
