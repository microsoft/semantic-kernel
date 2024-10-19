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
using Microsoft.SemanticKernel.Connectors.Ollama;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

public sealed class OllamaAutoFunctionChoiceBehaviorTests : BaseIntegrationTest
{
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;
    private readonly IChatCompletionService _chatCompletionService;

    public OllamaAutoFunctionChoiceBehaviorTests()
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

        List<string> invokedFunctions = [];

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        ChatHistory chatHistory = [];
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

        List<string> invokedFunctions = [];

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

        Assert.Contains("GetCurrentDate", invokedFunctions);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionManuallyAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        List<string> invokedFunctions = [];

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

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
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionAutomaticallyForStreamingShouldThrowAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        List<string> invokedFunctions = [];

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true) };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many days until Christmas?");

        string result = "";

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () =>
        {
            await foreach (var content in this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, this._kernel))
            {
                result += content;
            }
        });
    }

    [Fact]
    public async Task SpecifiedInPromptInstructsConnectorToInvokeKernelFunctionAutomaticallyForStreamingShouldThrowAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        List<string> invokedFunctions = [];

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

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () =>
        {
            await foreach (string c in promptFunction.InvokeStreamingAsync<string>(this._kernel))
            {
                result += c;
            }
        });
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionManuallyForStreamingShouldThrowAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        List<string> invokedFunctions = [];

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var functionsForManualInvocation = new List<string>();

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("How many days until Christmas?");

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () =>
        {
            await foreach (var content in this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, this._kernel))
            {
                foreach (var functionCallContent in content.Items.OfType<StreamingFunctionCallUpdateContent>().Where(fcc => !string.IsNullOrEmpty(fcc.Name)))
                {
                    functionsForManualInvocation.Add(functionCallContent.Name!);
                }
            }
        });
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeNonKernelFunctionManuallyAsync()
    {
        // Arrange
        var plugin = this._kernel.CreatePluginFromType<DateTimeUtils>(); // Creating plugin without importing it to the kernel.

        List<string> invokedFunctions = [];

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto([plugin.ElementAt(0)], autoInvoke: false) };

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

    private Kernel InitializeKernel()
    {
        var configuration = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ModelId!);
        Assert.NotNull(configuration.Endpoint);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOllamaChatCompletion(
            modelId: configuration.ModelId,
            endpoint: new Uri(configuration.Endpoint));

        return kernelBuilder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OllamaAutoFunctionChoiceBehaviorTests>()
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
