// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.SequentialPlanner;

public sealed class SequentialPlannerConfigFunctionTests : IDisposable
{
    public SequentialPlannerConfigFunctionTests(ITestOutputHelper output)
    {
        this._logger = NullLogger.Instance; //new XunitLogger<object>(output);
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SequentialPlannerConfigFunctionTests>()
            .Build();
    }

    // can supply a custom get available functions function (instead of using the extension methods on context and its Skills)
    [Fact]
    public Task CreatePlanWithCustomAvailableFunctionsAsync()
    {
        // TODO
        return Task.CompletedTask;
    }

    // TODO
    // can supply a custom get function function (instead of using the default context.Skills)

    // TODO
    // can supply both types of functions

    // Big Scenario
    // 1) Initialize service (load plugin manifest, populate vectordb) -- this would not be part of a hosted kernel service, could be done in a separate tool using same manifest
    // 2) Create kernel to run Planner, supply custom get available functions function to query vector store and supply custom get function function to import specific plugin from same manifest above into kernel
    [Fact]
    public async Task CreatePlanWithCustomAvailableFunctionsAndCustomFunctionAsync()
    {
        //
        // Arrange
        //
        var kernel = this.InitializeKernel(true);
        var emailSkill = kernel.ImportSkill(new EmailSkillFake());

        // TODO -- Why does this 403?
        // var klarnaSkill = await kernel.ImportChatGptPluginSkillFromUrlAsync("Klarna", new Uri("https://www.klarna.com/.well-known/ai-plugin.json")).ConfigureAwait(false);

        // create plugin manifest
        PluginManifest manifest = new();
        foreach (var kv in emailSkill/*.Union(klarnaSkill)*/)
        {
            // manifest.Plugins.Add(kv.Key, kv.Value);
            if (manifest.Plugins.TryGetValue(kv.Value.SkillName, out var value))
            {
                value.Functions.Add(kv.Value.Describe());
            }
            else
            {
                manifest.Plugins.Add(kv.Value.SkillName, new RemotePlugin()
                {
                    Url = new Uri("https://www.klarna.com/.well-known/ai-plugin.json"), // fake url for these
                    Functions = new System.Collections.Generic.List<FunctionView>() { kv.Value.Describe() }
                });
            }
        }

        // remember functions from a plugin manifest
        foreach (var function in manifest.Plugins.SelectMany(m => m.Value.Functions))
        {
            var functionName = function.ToFullyQualifiedName();
            var key = functionName;
            var description = string.IsNullOrEmpty(function.Description) ? functionName : function.Description;
            var textToEmbed = function.ToEmbeddingString();

            await kernel.Memory.SaveInformationAsync(collection: "CachedPluginsForPlanner", text: textToEmbed, id: key, description: description,
                additionalMetadata: JsonSerializer.Serialize(function)).ConfigureAwait(false);
        }

        //
        // Act
        //
        var config = new SequentialPlannerConfig
        {
            GetAvailableFunctionsAsync = async (config, semanticQuery) =>
            {
                // Search for functions that match the semantic query.
                var memories = kernel.Memory.SearchAsync("CachedPluginsForPlanner", semanticQuery!, config.MaxRelevantFunctions, 0.1);
                var relevantFunctions = new ConcurrentBag<FunctionView>();

                await foreach (var memoryEntry in memories)
                {
                    var functionView = JsonSerializer.Deserialize<FunctionView>(memoryEntry.Metadata.AdditionalMetadata);
                    if (functionView != null)
                    {
                        relevantFunctions.Add(functionView);
                    }
                }

                return relevantFunctions.OrderBy(x => x.SkillName).ThenBy(x => x.Name);
            },

            GetSkillFunction = (skillName, functionName) =>
            {
                // TODO -- load from manifest instead of using kernel.Skills.GetFunction
                return kernel.Skills.GetFunction(skillName, functionName);
            }
        };

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel, config);
        var plan = await planner.CreatePlanAsync("Let's have fun, use the first available tool for e-mail. Also use Klarna.");

        //
        // Assert
        //
        Assert.NotNull(plan);
        // TODO More validation, run the plan, etc.
        var result = await plan.InvokeAsync();
        await this._testOutputHelper.WriteLineAsync(result.Result);
    }

    private IKernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder.WithLogger(this._logger);

        if (useChatModel)
        {
            builder.WithAzureChatCompletionService(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder.WithAzureTextEmbeddingGenerationService(
                deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey)
                .WithMemoryStorage(new VolatileMemoryStore());
        }

        var kernel = builder.Build();

        // _ = kernel.ImportSkill(new EmailSkillFake());
        return kernel;
    }

    private readonly ILogger _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~SequentialPlannerConfigFunctionTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._logger is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}
