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

public static class Example22_OpenApiSkill_Jira
{
    private static string s_email = "aman.sachan@microsoft.com";
    private static string s_apiToken = Env.Var("JiraAPIToken");
    private static string s_serverURL = "https://skjiratest.atlassian.net/rest/api/latest/";
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
        var contextVariables = new ContextVariables();

        //string s_serverURL = "https://skjiratest.atlassian.net/rest/api/latest/"; // "https://<jiraProject>.atlassian.net/rest/api/latest/"
        contextVariables.Set("server-url", s_serverURL);

        IDictionary<string, ISKFunction> jiraSkills;
        var tokenProvider = new BasicAuthenticationProvider(AuthenticateWithBasicAPITokenAsync);

        bool bUseLocalFile = true;
        if (bUseLocalFile)
        {
            var apiSkillFile = "./Jira/apiDefinitionSimplified.json";
            jiraSkills = await kernel.ImportOpenApiSkillFromFileAsync("jiraSkills", apiSkillFile, tokenProvider.AuthenticateRequestAsync);
        }
        else
        {
            var apiSkillRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraSkills = await kernel.ImportOpenApiSkillFromUrlAsync("jiraSkills", apiSkillRawFileURL, null, tokenProvider.AuthenticateRequestAsync);
        }

        await RunJiraSkillsAsync(kernel, contextVariables, jiraSkills);
    }

    private static async Task RunJiraSkillsAsync(IKernel kernel, ContextVariables contextVars, IDictionary<string, ISKFunction> jiraSkills)
    {
        await GetIssueSkillAsync(kernel, jiraSkills, contextVars);
        await AddCommentSkillAsync(kernel, jiraSkills, contextVars);
    }

    private static async Task GetIssueSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //Set Properties for the Get Issue operation in the openAPI.swagger.json 
        contextVariables.Set("issueKey", "SKTES-2");

        //Run operation via the semantic kernel
        var result = await kernel.RunAsync(contextVariables, jiraSkills["GetIssue"]);

        Console.WriteLine("\n\n\n GetIssue jiraSkills response: \n{0}", result);
    }

    private static async Task AddCommentSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //Set Properties for the AddComment operation in the openAPI.swagger.json 
        contextVariables.Set("issueKey", "SKTES-1");
        contextVariables.Set("body", "Here is a rad comment");

        //Run operation via the semantic kernel
        var result = await kernel.RunAsync(contextVariables, jiraSkills["AddComment"]);

        Console.WriteLine("\n\n\n AddComment jiraSkills response: \n{0}", result);
    }

    // WARNING: we cant use the CreateIssueV2 Operation because the jira openAPI schema doesnt list properties under that operation name.
    // It seems like its dynamically creating that definition but we dont yet support the dynamic schema in SK
    /// <summary>
    /// 
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="jiraSkills"></param>
    /// <param name="contextVariables"></param>
    /// <returns></returns>
    private static async Task CreateIssueSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //Set Properties for the Create Issue path in the openAPI.swagger.json 
        contextVariables.Set("projectKey", "SKTES");
        contextVariables.Set("issueTypeIds", "Task");

        contextVariables.Set("item", "make the planet eco friendly");
        //Run Create Issue 
        var result = await kernel.RunAsync(contextVariables, jiraSkills["CreateIssueV2"]);

        Console.WriteLine("\n\n\n");
        Console.WriteLine("CreateIssueV2 jiraSkills response: \n{0}", result);
    }

    private static async Task ListIssuesSkillAsync(IKernel kernel, IDictionary<string, ISKFunction> jiraSkills, ContextVariables contextVariables)
    {
        //TODO this may need a custom implementation
        string serverURL;
        contextVariables.Get("server-url", serverURL);
        serverURL = s_serverURL + "search?jql="; // change search string

        contextVariables.Set("server-url", serverURL);
        //Set Properties for the Create Issue path in the openAPI.swagger.json 
        contextVariables.Set("projectKey", "SKTES");
        contextVariables.Set("issueTypeIds", "Task");
        contextVariables.Set("item", "make the planet eco friendly");
        //Run Create Issue 
        var result = await kernel.RunAsync(contextVariables, jiraSkills["CreateIssueV2"]);

        Console.WriteLine("\n\n\n CreateIssueV2 jiraSkills response: \n{0}", result);
    }

    private static Task<string> AuthenticateWithBasicAPITokenAsync()
    {
        string s = s_email + ":" + s_apiToken;
        return Task.FromResult(s);
    }

    /// <summary>
    /// Unit Test: Check if you can access jira via basic authentication; Does not use the Semantic Kernel.
    /// </summary>
    private static async Task Test_AccessJiraWithAPITokenAsync()
    {
        string serverURL = s_serverURL + "issue/SKTES-1";
        string s_token = Convert.ToBase64String(Encoding.UTF8.GetBytes($"{s_email}:{s_apiToken}"));

        var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", s_token);
        var response = await client.GetAsync(new Uri(serverURL));
        var content = await response.Content.ReadAsStringAsync();
        var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(content), Formatting.Indented);

        Console.WriteLine(formattedContent + "\n\n\n");
        client.Dispose();
    }
}
