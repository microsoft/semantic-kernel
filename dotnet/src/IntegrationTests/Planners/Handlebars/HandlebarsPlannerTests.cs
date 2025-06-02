// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Planning.Handlebars;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Planners.Handlebars;

public sealed class HandlebarsPlannerTests
{
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("Write a joke and send it in an e-mail to Kai.", "SendEmail", "test")]
    public async Task CreatePlanFunctionFlowAsync(string goal, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        var kernel = this.InitializeKernel(useEmbeddings);
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

    [RetryTheory(Skip = "This test is for manual verification.")]
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

    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("List each property of the default Qux object.", "## Complex types", """
        ### Qux:
        {
          "type": "Object",
          "properties": {
            "Bar": {
              "type": "String",
            },
            "Baz": {
              "type": "Int32",
            },
          }
        }
        """, "GetDefaultQux", "Foo")]
    public async Task CreatePlanWithComplexTypesDefinitionsAsync(string goal, string expectedSectionHeader, string expectedTypeHeader, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        var kernel = this.InitializeKernel(useEmbeddings);
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

    private Kernel InitializeKernel(bool useEmbeddings = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential());

        if (useEmbeddings)
        {
            builder.Services.AddAzureOpenAIEmbeddingGenerator(
                deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                modelId: azureOpenAIEmbeddingsConfiguration.EmbeddingModelId,
                endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                credentials: new AzureCliCredential());
        }

        return builder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<HandlebarsPlannerTests>()
        .Build();

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
        public sealed class Qux(string bar, int baz)
        {
            public string Bar { get; set; } = bar;
            public int Baz { get; set; } = baz;
        }

        [KernelFunction, Description("Returns default Qux object.")]
        public Qux GetDefaultQux() => new("bar", 42);
    }
}
