// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public sealed class PromptTests : IDisposable
{
    public PromptTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<PromptTests>()
            .Build();

        this._kernelBuilder = Kernel.CreateBuilder();
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
    }

    [Theory]
    [InlineData("SemanticKernel.IntegrationTests.prompts.GenerateStory.yaml", false)]
    [InlineData("SemanticKernel.IntegrationTests.prompts.GenerateStoryHandlebars.yaml", true)]
    public async Task GenerateStoryTestAsync(string resourceName, bool isHandlebars)
    {
        // Arrange
        var builder = this._kernelBuilder;
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
        Assert.True(actual.GetValue<string>()?.Length > 0);
    }

    #region private methods

    private readonly IKernelBuilder _kernelBuilder;
    private readonly IConfigurationRoot _configuration;
    private readonly XunitLogger<Kernel> _logger;

    public void Dispose()
    {
        this._logger.Dispose();
    }

    private void ConfigureAzureOpenAI(IKernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential(),
            serviceId: azureOpenAIConfiguration.ServiceId);
    }
    #endregion
}
