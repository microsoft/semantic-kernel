// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example22_OpenApiSkill
{
    public static async Task RunAsync()
    {
        await GetSecretFromAzureKeyVaultAsync();

        await AddSecretToAzureKeyVaultAsync();
    }

    public static async Task GetSecretFromAzureKeyVaultAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        //Import a OpenApi skill using one of the following Kernel extension methods
        //kernel.ImportOpenApiSkillFromResource
        //kernel.ImportOpenApiSkillFromDirectory
        //kernel.ImportOpenApiSkillFromFile
        //kernel.ImportOpenApiSkillFromUrlAsync
        //kernel.RegisterOpenApiSkill
        var skill = await kernel.ImportOpenApiSkillFromResourceAsync(SkillResourceNames.AzureKeyVault, AuthenticateWithBearerToken);

        //Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", "https://<keyvault-name>.vault.azure.net");
        contextVariables.Set("secret-name", "<secret-name>");
        contextVariables.Set("api-version", "7.0");

        //Run
        var result = await kernel.RunAsync(contextVariables, skill["GetSecret"]);

        Console.WriteLine("GetSecret skill response: {0}", result);
    }

    public static async Task AddSecretToAzureKeyVaultAsync()
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        //Import a OpenApi skill using one of the following Kernel extension methods
        //kernel.ImportOpenApiSkillFromResource
        //kernel.ImportOpenApiSkillFromDirectory
        //kernel.ImportOpenApiSkillFromFile
        //kernel.ImportOpenApiSkillFromUrlAsync
        //kernel.RegisterOpenApiSkill
        var skill = await kernel.ImportOpenApiSkillFromResourceAsync(SkillResourceNames.AzureKeyVault, AuthenticateWithBearerToken);

        //Add arguments for required parameters, arguments for optional ones can be skipped.
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

    private static Task AuthenticateWithBearerToken(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", Env.Var("AZURE_KEYVAULT_TOKEN"));
        return Task.CompletedTask;
    }
}
