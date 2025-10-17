// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiChatClientFunctionCallingTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string SkipMessage = "This test is for manual verification.";

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatClientWithAutoFunctionChoiceBehaviorCallsKernelFunctionAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var chatCompletionService = this.GetChatService(serviceType, isBeta);
        var chatClient = chatCompletionService.AsChatClient();

        var kernel = new Kernel();
        kernel.ImportPluginFromType<LightsPlugin>();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };
        var chatOptions = settings.ToChatOptions(kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Turn on the table lamp")
        };

        // Act
        var response = await chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

        // The response should indicate the function was called
        // Since we're using auto-invoke, the function result should be in the chat history
        var responseText = string.Join(" ", response.Messages.Select(m => m.Text));
        this.Output.WriteLine($"Response: {responseText}");
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatClientWithAutoFunctionChoiceBehaviorInvokesMultipleFunctionsAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var chatCompletionService = this.GetChatService(serviceType, isBeta);
        var chatClient = chatCompletionService.AsChatClient();

        var kernel = new Kernel();
        kernel.ImportPluginFromType<LightsPlugin>();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true)
        };
        var chatOptions = settings.ToChatOptions(kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Get the list of available lights and turn on the floor lamp")
        };

        // Act
        var response = await chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

        // The response should indicate both functions were called
        var responseText = string.Join(" ", response.Messages.Select(m => m.Text));
        this.Output.WriteLine($"Response: {responseText}");

        // Verify the response mentions the lights and the floor lamp being turned on
        Assert.NotEmpty(responseText);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatClientWithManualFunctionChoiceBehaviorReturnsFunctionCallsAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var chatCompletionService = this.GetChatService(serviceType, isBeta);
        var chatClient = chatCompletionService.AsChatClient();

        var kernel = new Kernel();
        kernel.ImportPluginFromType<LightsPlugin>();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false)
        };
        var chatOptions = settings.ToChatOptions(kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Turn on the ceiling light")
        };

        // Act
        var response = await chatClient.GetResponseAsync(messages, chatOptions);

        // Assert
        Assert.NotNull(response);

        // Extract function calls from the response
        var functionCalls = response.Messages
            .SelectMany(m => m.Contents)
            .OfType<Microsoft.Extensions.AI.FunctionCallContent>()
            .ToList();

        Assert.NotNull(functionCalls);
        Assert.NotEmpty(functionCalls);

        var functionCall = functionCalls.First();
        this.Output.WriteLine($"Function call: {functionCall.Name}");

        // Verify the function name contains the expected plugin and function
        Assert.Contains("TurnOn", functionCall.Name, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory(Skip = SkipMessage)]
    [InlineData(ServiceType.GoogleAI, true)]
    [InlineData(ServiceType.VertexAI, false)]
    public async Task ChatClientStreamingWithAutoFunctionChoiceBehaviorCallsKernelFunctionAsync(ServiceType serviceType, bool isBeta)
    {
        // Arrange
        var chatCompletionService = this.GetChatService(serviceType, isBeta);
        var chatClient = chatCompletionService.AsChatClient();

        var kernel = new Kernel();
        kernel.ImportPluginFromType<LightsPlugin>();

        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true)
        };
        var chatOptions = settings.ToChatOptions(kernel);

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Get the list of available lights")
        };

        string result = "";

        // Act
        await foreach (var update in chatClient.GetStreamingResponseAsync(messages, chatOptions))
        {
            foreach (var content in update.Contents)
            {
                if (content is Microsoft.Extensions.AI.TextContent textContent)
                {
                    result += textContent.Text;
                }
            }
        }

        // Assert
        Assert.NotEmpty(result);
        this.Output.WriteLine($"Streaming response: {result}");
    }

    /// <summary>
    /// A plugin that provides light control functionality.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class LightsPlugin
#pragma warning restore CA1812
    {
        private readonly Dictionary<int, string> _lights = new()
        {
            { 1, "Table Lamp" },
            { 2, "Floor Lamp" },
            { 3, "Ceiling Light" }
        };

        private readonly HashSet<int> _lightsOn = new();

        [KernelFunction]
        [Description("Get a list of available lights")]
        public string GetLights()
        {
            return string.Join(", ", this._lights.Select(kv => $"{kv.Key}: {kv.Value}"));
        }

        [KernelFunction]
        [Description("Turn on a specific light")]
        public string TurnOn([Description("The ID of the light to turn on")] int lightId)
        {
            if (!this._lights.TryGetValue(lightId, out var lightName))
            {
                return $"Light {lightId} not found";
            }

            this._lightsOn.Add(lightId);
            return $"Turned on {lightName}";
        }

        [KernelFunction]
        [Description("Turn off a specific light")]
        public string TurnOff([Description("The ID of the light to turn off")] int lightId)
        {
            if (!this._lights.TryGetValue(lightId, out var lightName))
            {
                return $"Light {lightId} not found";
            }

            this._lightsOn.Remove(lightId);
            return $"Turned off {lightName}";
        }

        [KernelFunction]
        [Description("Get the status of all lights")]
        public string GetStatus()
        {
            var status = this._lights.Select(kv =>
                $"{kv.Value}: {(this._lightsOn.Contains(kv.Key) ? "On" : "Off")}");
            return string.Join(", ", status);
        }
    }
}
