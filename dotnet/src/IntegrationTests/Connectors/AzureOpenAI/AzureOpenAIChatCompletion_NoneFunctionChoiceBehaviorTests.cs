// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

public sealed class AzureOpenAINoneFunctionChoiceBehaviorTests : BaseIntegrationTest, IDisposable
{
    private HttpClient? _httpClient;
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;

    public AzureOpenAINoneFunctionChoiceBehaviorTests()
    {
        this._autoFunctionInvocationFilter = new FakeFunctionFilter();

        this._kernel = this.InitializeKernel();
        this._kernel.AutoFunctionInvocationFilters.Add(this._autoFunctionInvocationFilter);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorNotToInvokeKernelFunctionAsync()
    {
        // Arrange
        var plugin = this._kernel.CreatePluginFromType<DateTimeUtils>();
        this._kernel.Plugins.Add(plugin);

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        // Act
        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };

        var result = await this._kernel.InvokePromptAsync("How many days until Christmas?", new(settings));

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorNotToInvokeKernelFunctionAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var promptTemplate = """"
            template_format: semantic-kernel
            template: How many days until Christmas?
            execution_settings:
              default:
                temperature: 0.1
                function_choice_behavior:
                  type: none
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        // Act
        var result = await this._kernel.InvokeAsync(promptFunction);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorNotToInvokeKernelFunctionForStreamingAsync()
    {
        // Arrange
        var plugin = this._kernel.CreatePluginFromType<DateTimeUtils>();
        this._kernel.Plugins.Add(plugin);

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new AzureOpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };

        StringBuilder result = new();

        // Act
        await foreach (string update in this._kernel.InvokePromptStreamingAsync<string>("How many days until Christmas?", new(settings)))
        {
            result.Append(update);
        }

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorNotToInvokeKernelFunctionForStreamingAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var promptTemplate = """"
            template_format: semantic-kernel
            template: How many days until Christmas?
            execution_settings:
              default:
                temperature: 0.1
                function_choice_behavior:
                  type: none
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        StringBuilder result = new();

        // Act
        await foreach (string update in promptFunction.InvokeStreamingAsync<string>(this._kernel))
        {
            result.Append(update);
        }

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);
    }

    public void Dispose()
    {
        this._httpClient?.Dispose();
    }

    private Kernel InitializeKernel()
    {
        this._httpClient ??= new() { Timeout = TimeSpan.FromSeconds(100) };
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential(),
            httpClient: this._httpClient);

        return kernelBuilder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIChatCompletionTests>()
        .Build();

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class DateTimeUtils
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [KernelFunction]
        [Description("Retrieves the current date.")]
        public string GetCurrentDate() => DateTime.UtcNow.ToString("d", CultureInfo.InvariantCulture);
    }

    #region private

    private sealed class FakeFunctionFilter : IAutoFunctionInvocationFilter
    {
        private Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? _onFunctionInvocation;

        public void RegisterFunctionInvocationHandler(Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> onFunctionInvocation)
        {
            this._onFunctionInvocation = onFunctionInvocation;
        }

        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            if (this._onFunctionInvocation is null)
            {
                return next(context);
            }

            return this._onFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
        }
    }

    #endregion
}
