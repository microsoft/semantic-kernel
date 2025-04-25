// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

public sealed class AzureOpenAIAutoFunctionChoiceBehaviorTests : BaseIntegrationTest
{
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;
    private readonly IChatCompletionService _chatCompletionService;

    public AzureOpenAIAutoFunctionChoiceBehaviorTests()
    {
        this._autoFunctionInvocationFilter = new FakeFunctionFilter();

        this._kernel = this.InitializeKernel();
        this._kernel.AutoFunctionInvocationFilters.Add(this._autoFunctionInvocationFilter);
        this._chatCompletionService = this._kernel.GetRequiredService<IChatCompletionService>();
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

        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

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
                function_choice_behavior:
                  type: auto
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        // Act
        var result = await this._kernel.InvokeAsync(promptFunction);

        // Assert
        Assert.NotNull(result);

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

        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var functionCalls = FunctionCallContent.GetFunctionCalls(result);
        Assert.NotNull(functionCalls);
        Assert.NotEmpty(functionCalls);

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

        var settings = new AzureOpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        string result = "";

        // Act
        await foreach (var content in this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, this._kernel))
        {
            result += content;
        }

        // Assert
        Assert.NotNull(result);

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
                function_choice_behavior:
                  type: auto
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

        var settings = new AzureOpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        await foreach (var content in this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, this._kernel))
        {
            if (content is OpenAIStreamingChatMessageContent openAIContent && openAIContent.ToolCallUpdates is { Count: > 0 } && !string.IsNullOrEmpty(openAIContent.ToolCallUpdates[0].FunctionName))
            {
                functionsForManualInvocation.Add(openAIContent.ToolCallUpdates[0].FunctionName);
            }
        }

        // Assert
        Assert.Contains("DateTimeUtils-GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeNonKernelFunctionManuallyAsync()
    {
        // Arrange
        var plugin = this._kernel.CreatePluginFromType<DateTimeUtils>(); // Creating plugin without importing it to the kernel.

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto([plugin.First()], autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var functionCalls = FunctionCallContent.GetFunctionCalls(result);
        Assert.NotNull(functionCalls);
        Assert.NotEmpty(functionCalls);

        var functionCall = functionCalls.First();
        Assert.Equal("DateTimeUtils", functionCall.PluginName);
        Assert.Equal("GetCurrentDate", functionCall.FunctionName);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeNonKernelFunctionManuallyForStreamingAsync()
    {
        // Arrange
        var plugin = this._kernel.CreatePluginFromType<DateTimeUtils>(); // Creating plugin without importing it to the kernel.

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var functionsForManualInvocation = new List<string>();

        var settings = new AzureOpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto([plugin.First()], autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        await foreach (var content in this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, this._kernel))
        {
            if (content is OpenAIStreamingChatMessageContent openAIContent && openAIContent.ToolCallUpdates is { Count: > 0 } && !string.IsNullOrEmpty(openAIContent.ToolCallUpdates[0].FunctionName))
            {
                functionsForManualInvocation.Add(openAIContent.ToolCallUpdates[0].FunctionName);
            }
        }

        // Assert
        Assert.Contains("DateTimeUtils-GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionsAutomaticallyConcurrentlyAsync()
    {
        // Arrange
        var requestIndexLog = new ConcurrentBag<int>();

        this._kernel.ImportPluginFromType<DateTimeUtils>();
        this._kernel.ImportPluginFromFunctions("WeatherUtils", [KernelFunctionFactory.CreateFromMethod(() => "Rainy day magic!", "GetCurrentWeather")]);

        var invokedFunctions = new ConcurrentBag<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            requestIndexLog.Add(context.RequestSequenceIndex);
            invokedFunctions.Add(context.Function.Name);

            await next(context);
        });

        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Give me today's date and weather.");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Contains("GetCurrentDate", invokedFunctions);
        Assert.Contains("GetCurrentWeather", invokedFunctions);

        Assert.True(requestIndexLog.All((item) => item == 0)); // Assert that all functions called by the AI model were executed within the same initial request.  
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task SpecifiedInCodeInstructsAIModelToCallFunctionInParallelOrSequentiallyAsync(bool callInParallel)
    {
        // Arrange
        var requestIndexLog = new ConcurrentBag<int>();

        this._kernel.ImportPluginFromType<DateTimeUtils>();
        this._kernel.ImportPluginFromFunctions("WeatherUtils", [KernelFunctionFactory.CreateFromMethod(() => "Rainy day magic!", "GetCurrentWeather")]);

        var invokedFunctions = new ConcurrentBag<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            requestIndexLog.Add(context.RequestSequenceIndex);
            invokedFunctions.Add(context.Function.Name);

            await next(context);
        });

        var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { AllowParallelCalls = callInParallel }) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Give me today's date and weather.");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Contains("GetCurrentDate", invokedFunctions);
        Assert.Contains("GetCurrentWeather", invokedFunctions);

        if (callInParallel)
        {
            // Assert that all functions are called within the same initial request.
            Assert.True(requestIndexLog.All((item) => item == 0));
        }
        else
        {
            // Assert that all functions are called in separate requests.
            Assert.Equal([0, 1], requestIndexLog);
        }
    }

    private Kernel InitializeKernel()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential());

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
