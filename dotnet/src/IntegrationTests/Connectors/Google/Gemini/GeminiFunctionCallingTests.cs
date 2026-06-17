// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Time.Testing;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiFunctionCallingTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string SkipMessage = "This test is for manual verification.";

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationEnabledFunctionsShouldReturnFunctionToCallAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>(nameof(CustomerPlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.EnableKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        var geminiResponse = response as GeminiChatMessageContent;
        Assert.NotNull(geminiResponse);
        Assert.NotNull(geminiResponse.ToolCalls);
        Assert.Single(geminiResponse.ToolCalls, item =>
            item.FullyQualifiedName == $"{nameof(CustomerPlugin)}{GeminiFunction.NameSeparator}{nameof(CustomerPlugin.GetCustomers)}");
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingEnabledFunctionsShouldReturnFunctionToCallAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>(nameof(CustomerPlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.EnableKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        Assert.Single(responses);
        var geminiResponse = responses[0] as GeminiStreamingChatMessageContent;
        Assert.NotNull(geminiResponse);
        Assert.NotNull(geminiResponse.ToolCalls);
        Assert.Single(geminiResponse.ToolCalls, item =>
            item.FullyQualifiedName == $"{nameof(CustomerPlugin)}{GeminiFunction.NameSeparator}{nameof(CustomerPlugin.GetCustomers)}");
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeShouldCallOneFunctionAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this.Output.WriteLine(response.Content);
        Assert.Contains("John Kowalski", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Anna Nowak", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Steve Smith", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeShouldCallOneFunctionAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("John Kowalski", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Anna Nowak", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Steve Smith", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeShouldCallTwoFunctionsAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers first and next return age of Anna customer?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this.Output.WriteLine(response.Content);
        Assert.Contains("28", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeShouldCallTwoFunctionsAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, could you show me list of customers first and next return age of Anna customer?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("28", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeShouldCallFunctionsMultipleTimesAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        kernel.ImportPluginFromType<MathPlugin>("MathPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(
            "Get list of customers and next get customers ages and at the end calculate the sum of ages of all customers.");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this.Output.WriteLine(response.Content);
        Assert.Contains("105", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeShouldCallFunctionsMultipleTimesAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");
        kernel.ImportPluginFromType<MathPlugin>("MathPlugin");
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(
            "Get list of customers and next get customers ages and at the end calculate the sum of ages of all customers.");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("105", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeNullablePropertiesWorksAsync(ServiceType serviceType, bool isBeta)
    {
        var kernel = new Kernel();
        kernel.ImportPluginFromType<NullableTestPlugin>();
        var sut = this.GetChatService(serviceType, isBeta);

        var executionSettings = new GeminiPromptExecutionSettings()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
        };

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("Hi, what's the weather in New York?");

        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings);

        Assert.NotNull(response);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeTwoPluginsShouldGetDateAndReturnTasksByDateParamAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<TaskPlugin>(nameof(TaskPlugin));
        kernel.ImportPluginFromType<DatePlugin>(nameof(DatePlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many tasks I have to do today? Show me count of tasks for today and date.");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this.Output.WriteLine(response.Content);
        Assert.Contains("5", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeTwoPluginsShouldGetDateAndReturnTasksByDateParamAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<TaskPlugin>(nameof(TaskPlugin));
        kernel.ImportPluginFromType<DatePlugin>(nameof(DatePlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("How many tasks I have to do today? Show me count of tasks for today and date.");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("5", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeTwoPluginsShouldGetDateAndReturnWeatherResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<DateTimePlugin>(nameof(DateTimePlugin));
        kernel.ImportPluginFromType<WeatherPlugin>(nameof(WeatherPlugin));
        kernel.ImportPluginFromType<TaskPlugin>(nameof(TaskPlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Whats the time and weather in Seattle?");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("sunny", content, StringComparison.OrdinalIgnoreCase);

        chatHistory.AddUserMessage("How many tasks I have for today, using the same date I checked weather in seattle");
        responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("5", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatGenerationAutoInvokeShouldCallFunctionWithEnumParameterAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        var timeProvider = new FakeTimeProvider();
        timeProvider.SetUtcNow(new DateTimeOffset(new DateTime(2024, 4, 24))); // Wednesday
        var timePlugin = new TimePlugin(timeProvider);
        kernel.ImportPluginFromObject(timePlugin, nameof(TimePlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("When was last friday? Show the date in format DD.MM.YYYY for example: 15.07.2019");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Assert
        this.Output.WriteLine(response.Content);
        Assert.Contains("19.04.2024", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatStreamingAutoInvokeShouldCallFunctionWithEnumParameterAndReturnResponseAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var kernel = new Kernel();
        var timeProvider = new FakeTimeProvider();
        timeProvider.SetUtcNow(new DateTimeOffset(new DateTime(2024, 4, 24))); // Wednesday
        var timePlugin = new TimePlugin(timeProvider);
        kernel.ImportPluginFromObject(timePlugin, nameof(TimePlugin));
        var sut = this.GetChatService(serviceType, isBeta);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("When was last friday? Show the date in format DD.MM.YYYY for example: 15.07.2019");
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 2000,
            ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel)
            .ToListAsync();

        // Assert
        string content = string.Concat(responses.Select(c => c.Content));
        this.Output.WriteLine(content);
        Assert.Contains("19.04.2024", content, StringComparison.OrdinalIgnoreCase);
    }

    public sealed class CustomerPlugin
    {
        [KernelFunction(nameof(GetCustomers))]
        [Description("Get list of customers.")]
        [return: Description("List of customers.")]
        public string[] GetCustomers()
        {
            return
            [
                "John Kowalski",
                "Anna Nowak",
                "Steve Smith",
            ];
        }

        [KernelFunction(nameof(GetCustomerAge))]
        [Description("Get age of customer.")]
        [return: Description("Age of customer.")]
        public int GetCustomerAge([Description("Name of customer")] string customerName)
        {
            return customerName switch
            {
                "John Kowalski" => 35,
                "Anna Nowak" => 28,
                "Steve Smith" => 42,
                _ => throw new ArgumentException("Customer not found."),
            };
        }
    }

    public sealed class TaskPlugin
    {
        [KernelFunction(nameof(GetTaskCount))]
        [Description("Get count of tasks for specific date.")]
        public int GetTaskCount([Description("Date to get tasks")] DateTime date)
        {
            return 5;
        }
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction(nameof(GetWeather))]
        [Description("Get the weather for a given location.")]
        public string GetWeather([Description("Location to get the weather for")] string location)
        {
            return $"The weather in {location} is sunny.";
        }
    }

    public sealed class DatePlugin
    {
        [KernelFunction(nameof(GetDate))]
        [Description("Get current (today) date.")]
#pragma warning disable CA1024
        public DateTime GetDate()
#pragma warning restore CA1024
        {
            return DateTime.Now.Date;
        }
    }

    public sealed class TimePlugin
    {
        private readonly TimeProvider _timeProvider;

        public TimePlugin(TimeProvider timeProvider)
        {
            this._timeProvider = timeProvider;
        }

        [KernelFunction]
        [Description("Get the date of the last day matching the supplied week day name in English. Example: Che giorno era 'Martedi' scorso -> dateMatchingLastDayName 'Tuesday' => Tuesday, 16 May, 2023")]
        public string DateMatchingLastDayName(
            [Description("The day name to match")] DayOfWeek input,
            IFormatProvider? formatProvider = null)
        {
            DateTimeOffset dateTime = this._timeProvider.GetUtcNow();

            // Walk backwards from the previous day for up to a week to find the matching day
            for (int i = 1; i <= 7; ++i)
            {
                dateTime = dateTime.AddDays(-1);
                if (dateTime.DayOfWeek == input)
                {
                    break;
                }
            }

            return dateTime.ToString("D", formatProvider);
        }
    }

    public sealed class DateTimePlugin
    {
        [KernelFunction(nameof(GetCurrentDateTime))]
        [Description("Get current UTC date and time.")]
        public string GetCurrentDateTime()
        {
            return DateTime.UtcNow.ToString("u");
        }
    }

    public sealed class MathPlugin
    {
        [KernelFunction(nameof(Sum))]
        [Description("Sum numbers.")]
        public int Sum([Description("Numbers to sum")] int[] numbers)
        {
            return numbers.Sum();
        }
    }

#pragma warning disable CA1812 // Uninstantiated internal types
    private sealed class NullableTestPlugin
    {
        [KernelFunction]
        [Description("Get the weather for a given location.")]
        private string GetWeather(Request request)
        {
            return $"The weather in {request?.Location} is sunny.";
        }
    }

    private sealed class Request
    {
        public string? Location { get; set; }
    }
#pragma warning disable CA1812 // Uninstantiated internal types
}
