// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

/**
 * This example shows how to use OpenAPI ChatGPT retrieval plugin
 * Plugin: https://github.com/openai/chatgpt-retrieval-plugin
 */
/** Setup **

# ----------------------------------------------------------------
git clone https://github.com/openai/chatgpt-retrieval-plugin
cd chatgpt-retrieval-plugin
cp examples/memory/ai-plugin.json .well-known/ai-plugin.json
cp examples/memory/openapi.yaml .well-known/openapi.yaml

# ----------------------------------------------------------------
# using python 3.10+
python -m pip install --upgrade poetry
poetry env use python3.10
poetry shell
poetry install

# ----------------------------------------------------------------
export OPENAI_API_KEY=sk-...
export BEARER_TOKEN=something

export DATASTORE=azuresearch

export AZURESEARCH_SERVICE=...
export AZURESEARCH_API_KEY=...
export AZURESEARCH_INDEX=chatgptretrievalplugin


export OPENAI_API_TYPE=azure
export OPENAI_API_BASE=https://....openai.azure.com/
export OPENAI_EMBEDDINGMODEL_DEPLOYMENTID=text-embedding-ada-002
export OPENAI_METADATA_EXTRACTIONMODEL_DEPLOYMENTID=gpt-4-32k
export OPENAI_COMPLETIONMODEL_DEPLOYMENTID=gpt-4-32k
export OPENAI_EMBEDDING_BATCH_SIZE=1
# ----------------------------------------------------------------

# This will start the plugin backend locally
poetry run start

# Plugin manifest:  http://127.0.0.1:8000/.well-known/ai-plugin.json
# OpenAPI manifest: http://127.0.0.1:8000/openapi.json

Run Program.cs, example 65

*/
// ReSharper disable once InconsistentNaming
public static class Example65_OpenAPI
{
    private const string BearerToken = "something";
    private const string APIUrl = "http://127.0.0.1:8000/";
    private const string OpenapiManifest = "http://127.0.0.1:8000/openapi.json";

    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync()
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var tokenProvider = new BasicAuthenticationProvider(() => Task.FromResult(BearerToken));

        using HttpClient httpClient = new();
        IDictionary<string, ISKFunction> plugin = await kernel.ImportOpenApiPluginFunctionsAsync(
            "memory",
            new Uri(OpenapiManifest),
            new OpenApiFunctionExecutionParameters(
                httpClient: httpClient,
                authCallback: tokenProvider.AuthenticateRequestAsync,
                serverUrlOverride: new Uri(APIUrl),
                operationsToExclude: new List<string> { "upsert_file_upsert_file_post" }));

        foreach (KeyValuePair<string, ISKFunction> foo in plugin)
        {
            Console.WriteLine($"* Imported function: {foo.Value.PluginName}.{foo.Value.Name} ({foo.Value.Description})");
        }

        ISKFunction upsertFunction = kernel.Functions.GetFunction("memory", "upsert_upsert_post");
        ISKFunction queryFunction = kernel.Functions.GetFunction("memory", "query_main_query_post");

        // This fails with:
        // Unhandled exception. System.Collections.Generic.KeyNotFoundException:
        // No variable found in context to use as an argument for the 'payload' parameter of the 'memory.upsert_upsert_post' Rest function.
        SKContext context0 = kernel.CreateNewContext();
        context0.Variables.Set("content", "the ast two Formula 1 races in 2023 will Las Vegas and Abu Dhabi");
        await upsertFunction.InvokeAsync(context0);

        // This fails with:
        // Unhandled exception. Microsoft.SemanticKernel.Diagnostics.HttpOperationException:
        // Response status code does not indicate success: 422 (Unprocessable Entity).
        SKContext context1 = kernel.CreateNewContext();
        context1.Variables.Set("payload", "the ast two Formula 1 races in 2023 will Las Vegas and Abu Dhabi");
        await upsertFunction.InvokeAsync(context1);

        // TODO:
        // 1. Define the correct syntax to pass text payload
        // 2. Verify that queryFunction works as expected
        // 3. Support upsert_file_upsert_file_post, ie uploading files
    }
}
