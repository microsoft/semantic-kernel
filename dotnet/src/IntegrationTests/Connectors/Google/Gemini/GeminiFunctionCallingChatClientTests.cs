// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using xRetry;
using Xunit;
using Xunit.Abstractions;
using AIFunctionCallContent = Microsoft.Extensions.AI.FunctionCallContent;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiFunctionCallingChatClientTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string SkipMessage = "This test is for manual verification.";

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ChatClientWithFunctionCallingReturnsToolCallsAsync(bool isVertexAI)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>(nameof(CustomerPlugin));

        var sut = this.GetChatClient(isVertexAI);

        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, could you show me list of customers?")
        };

        var tools = kernel.Plugins
            .SelectMany(p => p)
            .Select(f => f.AsAIFunction())
            .Cast<AITool>()
            .ToList();

        var chatOptions = new ChatOptions
        {
            Tools = tools
        };

        // Act
        var response = await sut.GetResponseAsync(chatHistory, chatOptions);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Messages);
        Assert.NotEmpty(response.Messages);

        var functionCallContent = response.Messages
            .SelectMany(m => m.Contents)
            .OfType<AIFunctionCallContent>()
            .FirstOrDefault();

        Assert.NotNull(functionCallContent);
        Assert.Contains("GetCustomers", functionCallContent.Name, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ChatClientStreamingWithFunctionCallingReturnsToolCallsAsync(bool isVertexAI)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>(nameof(CustomerPlugin));

        var sut = this.GetChatClient(isVertexAI);

        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, could you show me list of customers?")
        };

        var tools = kernel.Plugins
            .SelectMany(p => p)
            .Select(f => f.AsAIFunction())
            .Cast<AITool>()
            .ToList();

        var chatOptions = new ChatOptions
        {
            Tools = tools
        };

        // Act
        var responses = await sut.GetStreamingResponseAsync(chatHistory, chatOptions).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);

        var functionCallContent = responses
            .SelectMany(r => r.Contents)
            .OfType<AIFunctionCallContent>()
            .FirstOrDefault();

        Assert.NotNull(functionCallContent);
        Assert.Contains("GetCustomers", functionCallContent.Name, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ChatClientWithAutoInvokeFunctionsAsync(bool isVertexAI)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");

        var sut = this.GetChatClient(isVertexAI);

        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, could you show me list of customers?")
        };

        var tools = kernel.Plugins
            .SelectMany(p => p)
            .Select(f => f.AsAIFunction())
            .Cast<AITool>()
            .ToList();

        var chatOptions = new ChatOptions
        {
            Tools = tools,
            ToolMode = ChatToolMode.Auto
        };

        // Use FunctionInvokingChatClient for auto-invoke
        var autoInvokingClient = new FunctionInvokingChatClient(sut);

        // Act
        var response = await autoInvokingClient.GetResponseAsync(chatHistory, chatOptions);

        // Assert
        Assert.NotNull(response);
        var content = string.Join("", response.Messages.Select(m => m.Text));
        this.Output.WriteLine(content);
        Assert.Contains("John Kowalski", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Anna Nowak", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Steve Smith", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ChatClientStreamingWithAutoInvokeFunctionsAsync(bool isVertexAI)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");

        var sut = this.GetChatClient(isVertexAI);

        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, could you show me list of customers?")
        };

        var tools = kernel.Plugins
            .SelectMany(p => p)
            .Select(f => f.AsAIFunction())
            .Cast<AITool>()
            .ToList();

        var chatOptions = new ChatOptions
        {
            Tools = tools,
            ToolMode = ChatToolMode.Auto
        };

        // Use FunctionInvokingChatClient for auto-invoke
        var autoInvokingClient = new FunctionInvokingChatClient(sut);

        // Act
        var responses = await autoInvokingClient.GetStreamingResponseAsync(chatHistory, chatOptions).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        var content = string.Concat(responses.Select(c => c.Text));
        this.Output.WriteLine(content);
        Assert.Contains("John Kowalski", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Anna Nowak", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Steve Smith", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ChatClientWithMultipleFunctionCallsAsync(bool isVertexAI)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<CustomerPlugin>("CustomerPlugin");

        var sut = this.GetChatClient(isVertexAI);

        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, could you show me list of customers first and next return age of Anna customer?")
        };

        var tools = kernel.Plugins
            .SelectMany(p => p)
            .Select(f => f.AsAIFunction())
            .Cast<AITool>()
            .ToList();

        var chatOptions = new ChatOptions
        {
            Tools = tools,
            ToolMode = ChatToolMode.Auto
        };

        // Use FunctionInvokingChatClient for auto-invoke
        var autoInvokingClient = new FunctionInvokingChatClient(sut);

        // Act
        var response = await autoInvokingClient.GetResponseAsync(chatHistory, chatOptions);

        // Assert
        Assert.NotNull(response);
        var content = string.Join("", response.Messages.Select(m => m.Text));
        this.Output.WriteLine(content);
        Assert.Contains("28", content, StringComparison.OrdinalIgnoreCase);
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

    public sealed class MathPlugin
    {
        [KernelFunction(nameof(Sum))]
        [Description("Sum numbers.")]
        public int Sum([Description("Numbers to sum")] int[] numbers)
        {
            return numbers.Sum();
        }
    }
}
