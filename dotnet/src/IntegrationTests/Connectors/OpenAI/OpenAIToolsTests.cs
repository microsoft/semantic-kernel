// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.Planners.Stepwise;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIToolsTests : BaseIntegrationTest, IDisposable
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

    [Fact(Skip = "OpenAI is throttling requests. Switch this test to use Azure OpenAI.")]
    public async Task CanAutoInvokeKernelFunctionsAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<TimeInformation>();

        var invokedFunctions = new List<string>();

#pragma warning disable CS0618 // Events are deprecated
        void MyInvokingHandler(object? sender, FunctionInvokingEventArgs e)
        {
            invokedFunctions.Add(e.Function.Name);
        }

        kernel.FunctionInvoking += MyInvokingHandler;
#pragma warning restore CS0618 // Events are deprecated

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("GetCurrentUtcTime", invokedFunctions);
    }

    [Fact(Skip = "OpenAI is throttling requests. Switch this test to use Azure OpenAI.")]
    public async Task CanAutoInvokeKernelFunctionsStreamingAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<TimeInformation>();

        var invokedFunctions = new List<string>();

#pragma warning disable CS0618 // Events are deprecated
        void MyInvokingHandler(object? sender, FunctionInvokingEventArgs e)
        {
            invokedFunctions.Add($"{e.Function.Name}({string.Join(", ", e.Arguments)})");
        }

        kernel.FunctionInvoking += MyInvokingHandler;
#pragma warning restore CS0618 // Events are deprecated

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

    [Fact(Skip = "OpenAI is throttling requests. Switch this test to use Azure OpenAI.")]
    public async Task CanAutoInvokeKernelFunctionsWithComplexTypeParametersAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<WeatherPlugin>();

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await kernel.InvokePromptAsync("What is the current temperature in Dublin, Ireland, in Fahrenheit?", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("42.8", result.GetValue<string>(), StringComparison.InvariantCulture); // The WeatherPlugin always returns 42.8 for Dublin, Ireland.
    }

    [Fact(Skip = "OpenAI is throttling requests. Switch this test to use Azure OpenAI.")]
    public async Task CanAutoInvokeKernelFunctionsWithPrimitiveTypeParametersAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.ImportPluginFromType<WeatherPlugin>();

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await kernel.InvokePromptAsync("Convert 50 degrees Fahrenheit to Celsius.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("10", result.GetValue<string>(), StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionFromPromptAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();

        var promptFunction = KernelFunctionFactory.CreateFromPrompt(
            "Your role is always to return this text - 'A Game-Changer for the Transportation Industry'. Don't ask for more details or context.",
            functionName: "FindLatestNews",
            description: "Searches for the latest news.");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions(
            "NewsProvider",
            "Delivers up-to-date news content.",
            new[] { promptFunction }));

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var result = await kernel.InvokePromptAsync("Show me the latest news as they are.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Transportation", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionFromPromptStreamingAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();

        var promptFunction = KernelFunctionFactory.CreateFromPrompt(
            "Your role is always to return this text - 'A Game-Changer for the Transportation Industry'. Don't ask for more details or context.",
            functionName: "FindLatestNews",
            description: "Searches for the latest news.");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions(
            "NewsProvider",
            "Delivers up-to-date news content.",
            new[] { promptFunction }));

        // Act
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        var streamingResult = kernel.InvokePromptStreamingAsync("Show me the latest news as they are.", new(settings));

        var builder = new StringBuilder();

        await foreach (var update in streamingResult)
        {
            builder.Append(update.ToString());
        }

        var result = builder.ToString();

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Transportation", result, StringComparison.InvariantCultureIgnoreCase);
    }

    private Kernel InitializeKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = this.CreateKernelBuilder()
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

    public class WeatherPlugin
    {
        [KernelFunction, Description("Get current temperature.")]
        public Task<double> GetCurrentTemperatureAsync(WeatherParameters parameters)
        {
            if (parameters.City.Name == "Dublin" && (parameters.City.Country == "Ireland" || parameters.City.Country == "IE"))
            {
                return Task.FromResult(42.8); // 42.8 Fahrenheit.
            }

            throw new NotSupportedException($"Weather in {parameters.City.Name} ({parameters.City.Country}) is not supported.");
        }

        [KernelFunction, Description("Convert temperature from Fahrenheit to Celsius.")]
        public Task<double> ConvertTemperatureAsync(double temperatureInFahrenheit)
        {
            double temperatureInCelsius = (temperatureInFahrenheit - 32) * 5 / 9;
            return Task.FromResult(temperatureInCelsius);
        }
    }

    public record WeatherParameters(City City);

    public class City
    {
        public string Name { get; set; } = string.Empty;
        public string Country { get; set; } = string.Empty;
    }
}
