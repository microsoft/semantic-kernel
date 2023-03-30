// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using RepoUtils;

namespace KernelSyntaxExamples;
internal class Example20_OpenApiSkill
{
    public static async Task RunAsync()
    {
        await GetSecretFromAzureKeyValueAsync();

        await AddSecretToAzureKeyValutAsync();
    }

    public static async Task GetSecretFromAzureKeyValueAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        //Import
        var skill = kernel.ImportOpenApiSkillFromResource(SkillResourceNames.AzureKeyVault);

        //Add arguments
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", "https://<keyvault-name>.vault.azure.net");
        contextVariables.Set("secret-name", "<secret-name>");
        contextVariables.Set("api-version", "7.0");

        //Run
        var result = await kernel.RunAsync(contextVariables, skill["GetSecret"]);

        Console.WriteLine("GetSecret skill response: {0}", result);
    }

    public static async Task AddSecretToAzureKeyValutAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        //Import
        var skill = kernel.ImportOpenApiSkillFromResource(SkillResourceNames.AzureKeyVault);

        //Add arguments
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", "https://<keyvault-name>.vault.azure.net");
        contextVariables.Set("secret-name", "<secret-name>");
        contextVariables.Set("api-version", "7.0");
        contextVariables.Set("enabled", "true");
        contextVariables.Set("value", "<secret>");

        //Run
        var result = await kernel.RunAsync(contextVariables, skill["SetSecret"]);

        Console.WriteLine("SetSecret skill response: {0}", result);
    }
}
