// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIChatClientRequiredFunctionChoiceBehaviorTests : BaseIntegrationTest
{
    private readonly Kernel _kernel;
    private readonly FakeFunctionFilter _autoFunctionInvocationFilter;
    private readonly IChatClient _chatClient;

    public OpenAIChatClientRequiredFunctionChoiceBehaviorTests()
    {
        this._autoFunctionInvocationFilter = new FakeFunctionFilter();

        this._kernel = this.InitializeKernel();
        this._kernel.AutoFunctionInvocationFilters.Add(this._autoFunctionInvocationFilter);
        this._chatClient = this._kernel.GetRequiredService<IChatClient>();
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeRequiredFunctionAutomaticallyForStreamingAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: true) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        var response = await this._chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

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
                  type: required
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

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: false) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        var response = await this._chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

        Assert.Empty(invokedFunctions);

        // Extract function calls from the response
        var functionCalls = response.Messages
            .SelectMany(m => m.Contents)
            .OfType<Microsoft.Extensions.AI.FunctionCallContent>()
            .ToList();

        Assert.NotNull(functionCalls);
        Assert.NotEmpty(functionCalls);

        var functionCall = functionCalls.First();
        Assert.Equal("DateTimeUtils", functionCall.Name.Split('_')[0]);
        Assert.Equal("GetCurrentDate", functionCall.Name.Split('_')[1]);
    }

    [Fact]
    public async Task SpecifiedInCodeInstructsConnectorToInvokeKernelFunctionAutomaticallyForStreamingAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<DateTimeUtils>();

        var invokedFunctions = new List<string?>();

        this._autoFunctionInvocationFilter.RegisterFunctionInvocationHandler(async (context, next) =>
            {
                invokedFunctions.Add(context.Function.Name);
                await next(context);
            });

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: true) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        await foreach (var update in this._chatClient.GetStreamingResponseAsync(messages, chatOptions))
        {
            // Process streaming updates
        }

        // Assert
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
                  type: required
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

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: false) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        await foreach (var update in this._chatClient.GetStreamingResponseAsync(messages, chatOptions))
        {
            foreach (var content in update.Contents)
            {
                if (content is Microsoft.Extensions.AI.FunctionCallContent functionCall && !string.IsNullOrEmpty(functionCall.Name))
                {
                    functionsForManualInvocation.Add(functionCall.Name);
                }
            }
        }

        // Assert
        Assert.Contains("DateTimeUtils_GetCurrentDate", functionsForManualInvocation);

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

        var settings = new OpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required([plugin.ElementAt(0)], autoInvoke: false) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        var response = await this._chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

        Assert.Empty(invokedFunctions);

        // Extract function calls from the response
        var functionCalls = response.Messages
            .SelectMany(m => m.Contents)
            .OfType<Microsoft.Extensions.AI.FunctionCallContent>()
            .ToList();

        Assert.NotNull(functionCalls);
        Assert.NotEmpty(functionCalls);

        var functionCall = functionCalls.First();
        Assert.Equal("DateTimeUtils", functionCall.Name.Split('_')[0]);
        Assert.Equal("GetCurrentDate", functionCall.Name.Split('_')[1]);
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

        var settings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Required([plugin.ElementAt(0)], autoInvoke: false) };
        var chatOptions = settings.ToChatOptions(this._kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "How many days until Christmas?")
        };

        // Act
        await foreach (var update in this._chatClient.GetStreamingResponseAsync(messages, chatOptions))
        {
            foreach (var content in update.Contents)
            {
                if (content is Microsoft.Extensions.AI.FunctionCallContent functionCall && !string.IsNullOrEmpty(functionCall.Name))
                {
                    functionsForManualInvocation.Add(functionCall.Name);
                }
            }
        }

        // Assert
        Assert.Contains("DateTimeUtils_GetCurrentDate", functionsForManualInvocation);

        Assert.Empty(invokedFunctions);
    }

    private Kernel InitializeKernel()
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ChatModelId);
        Assert.NotNull(openAIConfiguration.ApiKey);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOpenAIChatClient(
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

    #region private

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
