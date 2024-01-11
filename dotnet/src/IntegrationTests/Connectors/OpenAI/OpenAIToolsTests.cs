// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
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

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsStreamingAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<TimeInformation>();

        var invokedFunctions = new List<string>();
        void MyInvokingHandler(object? sender, FunctionInvokingEventArgs e)
        {
            invokedFunctions.Add($"{e.Function.Name}({string.Join(", ", e.Arguments)})");
        }
        kernel.FunctionInvoking += MyInvokingHandler;

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        string result = "";
        await foreach (string c in kernel.InvokePromptStreamingAsync<string>(
            $"How much older is John than Jim? Compute that value and pass it to the {nameof(TimeInformation)}.{nameof(TimeInformation.InterpretValue)} function, then respond only with its result.",
            new(settings)))
        {
            result += c;
        }

        // Assert
        Assert.Contains("6", result, StringComparison.InvariantCulture);
        Assert.Contains("GetAge([personName, John])", invokedFunctions);
        Assert.Contains("GetAge([personName, Jim])", invokedFunctions);
        Assert.Contains("InterpretValue([value, 3])", invokedFunctions);
    }

    private Kernel InitializeKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey);

        var kernel = builder.Build();

        return kernel;
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose() => this._testOutputHelper.Dispose();

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation
    {
        [KernelFunction]
        [Description("Retrieves the current time in UTC.")]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");

        [KernelFunction]
        [Description("Gets the age of the specified person.")]
        public int GetAge(string personName)
        {
            if ("John".Equals(personName, StringComparison.OrdinalIgnoreCase))
            {
                return 33;
            }

            if ("Jim".Equals(personName, StringComparison.OrdinalIgnoreCase))
            {
                return 30;
            }

            return -1;
        }

        [KernelFunction]
        public int InterpretValue(int value) => value * 2;
    }
}
