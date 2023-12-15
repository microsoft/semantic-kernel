// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.Planners.Stepwise;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIToolsTests : IDisposable
{
    public OpenAIToolsTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<FunctionCallingStepwisePlannerTests>()
            .Build();
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<TimeInformation>();

        var invokedFunctions = new List<string>();
        void MyInvokingHandler(object? sender, FunctionInvokingEventArgs e)
        {
            invokedFunctions.Add(e.Function.Name);
        }
        kernel.FunctionInvoking += MyInvokingHandler;

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("GetCurrentUtcTime", invokedFunctions);
    }

    private Kernel InitializeKernel()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("Planners:AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);

        var kernel = builder.Build();

        return kernel;
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~OpenAIToolsTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._testOutputHelper.Dispose();
        }
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation
    {
        [KernelFunction]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");
    }
}
