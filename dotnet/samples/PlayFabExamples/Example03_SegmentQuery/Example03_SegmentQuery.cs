// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Newtonsoft.Json;
using PlayFabExamples.Common.Configuration;
using PlayFabExamples.Common.Logging;

namespace PlayFabExamples.Example03_SegmentQuery;

/// <summary>
/// This example shows how to import PlayFab APIs as skills.
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example03_SegmentQuery
{
    public static async Task RunAsync()
    {
        await SkillImportExample();
    }

    private static async Task SkillImportExample()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Logger).Build();
        var contextVariables = new ContextVariables();

        contextVariables.Set("server_url", TestConfiguration.PlayFab.Endpoint);

        using HttpClient httpClient = new();

        var playfabApiSkills = await GetPlayFabSkill(kernel, httpClient);

        // GetSegments skill
        {
            // Set properties for the Get Segments operation in the openAPI.swagger.json
            contextVariables.Set("content_type", "application/json");
            contextVariables.Set("payload", "{ \"SegmentIds\": [] }");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, playfabApiSkills["GetSegments"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.Result), Formatting.Indented);
            Console.WriteLine("GetSegments playfabApiSkills response: \n{0}", formattedContent);
        }
    }

    private static async Task<IDictionary<string, ISKFunction>> GetPlayFabSkill(IKernel kernel, HttpClient httpClient)
    {
        IDictionary<string, ISKFunction> playfabApiSkills;

        var titleSecretKeyProvider = new PlayFabAuthenticationProvider(() =>
        {
            string s = TestConfiguration.PlayFab.TitleSecretKey;
            return Task.FromResult(s);
        });

        bool useLocalFile = true;
        if (useLocalFile)
        {
            var playfabApiFile = "../../../Skills/PlayFabApiSkill/openapi.json";
            playfabApiSkills = await kernel.ImportOpenApiSkillFromFileAsync("PlayFabApiSkill", playfabApiFile, new OpenApiSkillExecutionParameters(httpClient, authCallback: titleSecretKeyProvider.AuthenticateRequestAsync)); ;
        }
        else
        {
            var playfabApiRawFileUrl = new Uri(TestConfiguration.PlayFab.SwaggerEndpoint);
            playfabApiSkills = await kernel.ImportOpenApiSkillFromUrlAsync("PlayFabApiSkill", playfabApiRawFileUrl, new OpenApiSkillExecutionParameters(httpClient, authCallback: titleSecretKeyProvider.AuthenticateRequestAsync)); ;
        }

        return playfabApiSkills;
    }
}
