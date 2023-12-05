// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;
using SemanticKernel.IntegrationTests.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public sealed class PromptTests : IDisposable
{
    public PromptTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAICompletionTests>()
            .Build();

        this._kernelBuilder = new KernelBuilder();
    }

    [Theory]
    [InlineData("SemanticKernel.IntegrationTests.prompts.GenerateStory.yaml", false)]
    [InlineData("SemanticKernel.IntegrationTests.prompts.GenerateStoryHandlebars.yaml", true)]
    public async Task GenerateStoryTestAsync(string resourceName, bool isHandlebars)
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        var kernel = builder.Build();

        // Load prompt from resource
        var promptTemplateFactory = isHandlebars ? new HandlebarsPromptTemplateFactory() : null;
        using StreamReader reader = new(Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName)!);
        var function = kernel.CreateFunctionFromPromptYaml(await reader.ReadToEndAsync(), promptTemplateFactory);

        // Act
        FunctionResult actual = await kernel.InvokeAsync(function, arguments: new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            });

        // Assert
        Assert.Contains("Dog", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    #region private methods

    private readonly KernelBuilder _kernelBuilder;
    private readonly IConfigurationRoot _configuration;
    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~PromptTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
            this._testOutputHelper.Dispose();
        }
    }

    private void ConfigureAzureOpenAI(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.WithAzureOpenAITextGeneration(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }
    #endregion
}
