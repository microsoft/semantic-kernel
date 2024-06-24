// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Planning.Handlebars;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Handlebars;

public sealed class HandlebarsPlannerTests : IDisposable
{
    public HandlebarsPlannerTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<HandlebarsPlannerTests>()
            .Build();
    }

    [Theory]
    [InlineData(true, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "test")]
    public async Task CreatePlanFunctionFlowAsync(bool useChatModel, string goal, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        var kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        kernel.ImportPluginFromType<EmailPluginFake>(expectedPlugin);
        TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        var plan = await new HandlebarsPlanner(s_defaultPlannerOptions).CreatePlanAsync(kernel, goal);

        // Assert expected function
        Assert.Contains(
            $"{expectedPlugin}-{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    [RetryTheory]
    [InlineData("Write a novel about software development that is 3 chapters long.", "NovelChapter", "WriterPlugin")]
    public async Task CreatePlanWithDefaultsAsync(string goal, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        TestHelpers.ImportSamplePlugins(kernel, "WriterPlugin", "MiscPlugin");

        // Act
        var plan = await new HandlebarsPlanner(s_defaultPlannerOptions).CreatePlanAsync(kernel, goal);

        // Assert
        Assert.Contains(
            $"{expectedPlugin}-{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    [Theory]
    [InlineData(true, "List each property of the default Qux object.", "## Complex types", @"### Qux:
{
  ""type"": ""Object"",
  ""properties"": {
    ""Bar"": {
      ""type"": ""String"",
    },
    ""Baz"": {
      ""type"": ""Int32"",
    },
  }
}", "GetDefaultQux", "Foo")]
    public async Task CreatePlanWithComplexTypesDefinitionsAsync(bool useChatModel, string goal, string expectedSectionHeader, string expectedTypeHeader, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        var kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        kernel.ImportPluginFromObject(new Foo());

        // Act
        var plan = await new HandlebarsPlanner(s_defaultPlannerOptions).CreatePlanAsync(kernel, goal);

        // Assert expected section header for Complex Types in prompt
        Assert.Contains(
            expectedSectionHeader,
            plan.Prompt,
            StringComparison.CurrentCulture
        );

        // Assert expected complex parameter type in prompt
        Assert.Contains(
            expectedTypeHeader,
            plan.Prompt,
            StringComparison.CurrentCulture
        );

        // Assert expected function in plan
        Assert.Contains(
            $"{expectedPlugin}-{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    private Kernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = true)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();

        if (useChatModel)
        {
            builder.Services.AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                modelId: azureOpenAIConfiguration.ChatModelId!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.Services.AddAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                modelId: azureOpenAIConfiguration.ModelId,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder.Services.AddAzureOpenAITextEmbeddingGeneration(
                deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                modelId: azureOpenAIEmbeddingsConfiguration.EmbeddingModelId!,
                endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
        }

        return builder.Build();
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    private static readonly HandlebarsPlannerOptions s_defaultPlannerOptions = new()
    {
        ExecutionSettings = new OpenAIPromptExecutionSettings()
        {
            Temperature = 0.0,
            TopP = 0.1,
        }
    };

    private sealed class Foo
    {
        public sealed class Qux
        {
            public string Bar { get; set; } = string.Empty;
            public int Baz { get; set; }

            public Qux(string bar, int baz)
            {
                this.Bar = bar;
                this.Baz = baz;
            }
        }

        [KernelFunction, Description("Returns default Qux object.")]
        public Qux GetDefaultQux() => new("bar", 42);
    }

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
