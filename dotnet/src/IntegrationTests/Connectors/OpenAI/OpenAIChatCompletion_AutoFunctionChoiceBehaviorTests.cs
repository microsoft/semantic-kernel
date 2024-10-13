// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIAutoFunctionChoiceBehaviorTests : BaseIntegrationTest
{
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;
    private readonly IChatCompletionService _chatCompletionService;

    public OpenAIAutoFunctionChoiceBehaviorTests()
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

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(invokedFunctions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
            """";

        var promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplate);

        // Act
        var result = await this._kernel.InvokeAsync(promptFunction);

        // Assert
        Assert.NotNull(result);

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(invokedFunctions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var functionCalls = FunctionCallContent.GetFunctionCalls(result);
        Assert.NotNull(functionCalls);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(functionCalls);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        Assert.Single(functionCalls);
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

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

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(invokedFunctions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(invokedFunctions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(invokedFunctions);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(functionsForManualInvocation);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto([plugin.ElementAt(0)], autoInvoke: false) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act
        var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

        // Assert
        Assert.NotNull(result);

        Assert.Empty(invokedFunctions);

        var functionCalls = FunctionCallContent.GetFunctionCalls(result);
        Assert.NotNull(functionCalls);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(functionCalls);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        Assert.Single(functionCalls);
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        Assert.NotEmpty(functionCalls);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

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

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto([plugin.ElementAt(0)], autoInvoke: false) };

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Single(functionsForManualInvocation);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
        Assert.Single(functionsForManualInvocation);
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        Assert.Contains("DateTimeUtils-GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    private Kernel InitializeKernel()
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ChatModelId!);
        Assert.NotNull(openAIConfiguration.ApiKey);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOpenAIChatCompletion(
            modelId: openAIConfiguration.ChatModelId,
            apiKey: openAIConfiguration.ApiKey);

        return kernelBuilder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIChatCompletionTests>()
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
