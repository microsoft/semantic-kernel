// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Configuration;

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.Planners.Stepwise;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIAutoFunctionChoiceBehaviorTests : BaseIntegrationTest
{
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;

    public OpenAIAutoFunctionChoiceBehaviorTests()
    {
        this._autoFunctionInvocationFilter = new FakeFunctionFilter();

        this._kernel = this.InitializeKernel();
        this._kernel.AutoFunctionInvocationFilters.Add(this._autoFunctionInvocationFilter);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionAutomaticallyAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        // Act
        var settings = new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.AutoFunctionChoice(autoInvoke: true) };

        var result = await this._kernel.InvokePromptAsync("How many days until Christmas?", new(settings));

        // Assert
        Assert.NotNull(result);

        Assert.Single(invokedFunctions);
        Assert.Contains("GetCurrentDate", invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorToInvokeKernelFunctionAutomaticallyAsync()
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
                  type: auto
                  maximum_auto_invoke_attempts: 3
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        // Act
        var result = await this._kernel.InvokeAsync(promptFunction);

        // Assert
        Assert.NotNull(result);

        Assert.Single(invokedFunctions);
        Assert.Contains("GetCurrentDate", invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionManuallyAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        // Act
        var settings = new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.AutoFunctionChoice(autoInvoke: false) };

        var result = await this._kernel.InvokePromptAsync("How many days until Christmas?", new(settings));

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var responseContent = result.GetValue<ChatMessageContent>();
        Assert.NotNull(responseContent);

        var functionCalls = FunctionCallContent.GetFunctionCalls(responseContent);
        Assert.NotNull(functionCalls);
        Assert.Single(functionCalls);

        var functionCall = functionCalls.First();
        Assert.Equal("DateTimeUtils", functionCall.PluginName);
        Assert.Equal("GetCurrentDate", functionCall.FunctionName);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorToInvokeKernelFunctionManuallyAsync()
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
                  type: auto
                  maximum_auto_invoke_attempts: 0
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        // Act
        var result = await this._kernel.InvokeAsync(promptFunction);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var responseContent = result.GetValue<ChatMessageContent>();
        Assert.NotNull(responseContent);

        var functionCalls = FunctionCallContent.GetFunctionCalls(responseContent);
        Assert.NotNull(functionCalls);
        Assert.Single(functionCalls);

        var functionCall = functionCalls.First();
        Assert.Equal("DateTimeUtils", functionCall.PluginName);
        Assert.Equal("GetCurrentDate", functionCall.FunctionName);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionAutomaticallyForStreamingAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.AutoFunctionChoice(autoInvoke: true) };

        string result = "";

        // Act
        await foreach (string c in this._kernel.InvokePromptStreamingAsync<string>("How many days until Christmas?", new(settings)))
        {
            result += c;
        }

        // Assert
        Assert.NotNull(result);

        Assert.Single(invokedFunctions);
        Assert.Contains("GetCurrentDate", invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorToInvokeKernelFunctionAutomaticallyForStreamingAsync()
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
                  type: auto
                  maximum_auto_invoke_attempts: 3
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        string result = "";

        // Act
        await foreach (string c in promptFunction.InvokeStreamingAsync<string>(this._kernel))
        {
            result += c;
        }

        // Assert
        Assert.NotNull(result);

        Assert.Single(invokedFunctions);
        Assert.Contains("GetCurrentDate", invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionManuallyForStreamingAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var functionsForManualInvocation = new List<string>();

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.AutoFunctionChoice(autoInvoke: false) };

        // Act
        await foreach (var content in this._kernel.InvokePromptStreamingAsync<OpenAIStreamingChatMessageContent>("How many days until Christmas?", new(settings)))
        {
            if (content.ToolCallUpdate is StreamingFunctionToolCallUpdate functionUpdate && !string.IsNullOrEmpty(functionUpdate.Name))
            {
                functionsForManualInvocation.Add(functionUpdate.Name);
            }
        }

        // Assert
        Assert.Single(functionsForManualInvocation);
        Assert.Contains("DateTimeUtils-GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorToInvokeKernelFunctionManuallyForStreamingAsync()
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
                  type: auto
                  maximum_auto_invoke_attempts: 0
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        var functionsForManualInvocation = new List<string>();

        // Act
        await foreach (var content in promptFunction.InvokeStreamingAsync<OpenAIStreamingChatMessageContent>(this._kernel))
        {
            if (content.ToolCallUpdate is StreamingFunctionToolCallUpdate functionUpdate && !string.IsNullOrEmpty(functionUpdate.Name))
            {
                functionsForManualInvocation.Add(functionUpdate.Name);
            }
        }

        // Assert
        Assert.Single(functionsForManualInvocation);
        Assert.Contains("DateTimeUtils-GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    private Kernel InitializeKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = this.CreateKernelBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey);

        return builder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<FunctionCallingStepwisePlannerTests>()
        .Build();

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class DateTimeUtils
    {
        [KernelFunction]
        [Description("Retrieves the current time in UTC.")]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");

        [KernelFunction]
        [Description("Retrieves the current date.")]
        public string GetCurrentDate() => DateTime.UtcNow.ToString("d", CultureInfo.InvariantCulture);
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

        [KernelFunction, Description("Get the current weather for the specified city.")]
        public Task<string> GetWeatherForCityAsync(string cityName)
        {
            return Task.FromResult(cityName switch
            {
                "Boston" => "61 and rainy",
                _ => "31 and snowing",
            });
        }
    }

    public record WeatherParameters(City City);

    public class City
    {
        public string Name { get; set; } = string.Empty;
        public string Country { get; set; } = string.Empty;
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
