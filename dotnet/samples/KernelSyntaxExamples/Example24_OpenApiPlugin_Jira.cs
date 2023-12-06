// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Authentication;
using Microsoft.SemanticKernel.Plugins.OpenApi.Model;

// ReSharper disable once InconsistentNaming
public static class Example24_OpenApiPlugin_Jira
{
    /// <summary>
    /// This sample shows how to connect the Semantic Kernel to Jira as an Open API plugin based on the Open API schema.
    /// This format of registering the plugin and its operations, and subsequently executing those operations can be applied
    /// to an Open API plugin that follows the Open API Schema.
    /// To use this example, there are a few requirements:
    /// 1. You must have a Jira instance that you can authenticate to with your email and api key.
    ///    Follow the instructions here to get your api key:
    ///    https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
    /// 2. You must create a new project in your Jira instance and create two issues named TEST-1 and TEST-2 respectively.
    ///    Follow the instructions here to create a new project and issues:
    ///    https://support.atlassian.com/jira-software-cloud/docs/create-a-new-project/
    ///    https://support.atlassian.com/jira-software-cloud/docs/create-an-issue-and-a-sub-task/
    /// 3. You can find your domain under the "Products" tab in your account management page.
    ///    To go to your account management page, click on your profile picture in the top right corner of your Jira
    ///    instance then select "Manage account".
    /// 4. Configure the secrets as described by the ReadMe.md in the dotnet/samples/KernelSyntaxExamples folder.
    /// </summary>
    public static async Task RunAsync()
    {
        Kernel kernel = new();

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";

        IKernelPlugin jiraFunctions;
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
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginFile,
                new OpenApiFunctionExecutionParameters(
                    authCallback: tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
        }
        else
        {
            var apiPluginRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginRawFileURL,
                new OpenApiFunctionExecutionParameters(
                    httpClient, tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
        }

        var arguments = new KernelArguments();

        // GetIssue Function
        // Set Properties for the Get Issue operation in the openAPI.swagger.json
        // Make sure the issue exists in your Jira instance or it will return a 404
        arguments["issueKey"] = "TEST-1";

        // Run operation via the semantic kernel
        var result = await kernel.InvokeAsync(jiraFunctions["GetIssue"], arguments);

        Console.WriteLine("\n\n\n");
        var formattedContent = JsonSerializer.Serialize(
            result.GetValue<RestApiOperationResponse>(),
            new JsonSerializerOptions()
            {
                WriteIndented = true
            });
        Console.WriteLine("GetIssue jiraPlugin response: \n{0}", formattedContent);

        // AddComment Function
        arguments["issueKey"] = "TEST-2";
        arguments[RestApiOperation.PayloadArgumentName] = "{\"body\": \"Here is a rad comment\"}";

        // Run operation via the semantic kernel
        result = await kernel.InvokeAsync(jiraFunctions["AddComment"], arguments);

        Console.WriteLine("\n\n\n");

        formattedContent = JsonSerializer.Serialize(
            result.GetValue<RestApiOperationResponse>(),
            new JsonSerializerOptions()
            {
                WriteIndented = true
            });
        Console.WriteLine("AddComment jiraPlugin response: \n{0}", formattedContent);
    }
}
