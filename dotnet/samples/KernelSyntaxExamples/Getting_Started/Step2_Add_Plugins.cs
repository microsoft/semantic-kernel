// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

/// <summary>
/// This example shows how to load a <see cref="KernelPlugin"/> instances.
/// </summary>
public sealed class Step2_Add_Plugins : BaseTest
{
    /// <summary>
    /// Shows different ways to load a <see cref="KernelPlugin"/> instances.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<TimeInformation>();
        kernelBuilder.Plugins.AddFromType<WidgetFactory>();
        Kernel kernel = kernelBuilder.Build();

        // Example 1. Invoke the kernel with a prompt that asks the AI for information it cannot provide and may hallucinate
        WriteLine(await kernel.InvokePromptAsync("How many days until Christmas?"));

        // Example 2. Invoke the kernel with a templated prompt that invokes a plugin and display the result
        WriteLine(await kernel.InvokePromptAsync("The current time is {{TimeInformation.GetCurrentUtcTime}}. How many days until Christmas?"));

        // Example 3. Invoke the kernel with a prompt and allow the AI to automatically invoke functions
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        WriteLine(await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.", new(settings)));

        // Example 4. Invoke the kernel with a prompt and allow the AI to automatically invoke functions that use enumerations
        WriteLine(await kernel.InvokePromptAsync("Create a handy lime colored widget for me.", new(settings)));
        WriteLine(await kernel.InvokePromptAsync("Create a beautiful scarlet colored widget for me.", new(settings)));
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation
    {
        [KernelFunction]
        [Description("Retrieves the current time in UTC.")]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class WidgetFactory
    {
        [KernelFunction]
        [Description("Creates a new widget of the specified type and color")]
        public WidgetDetails CreateWidget([Description("The type of widget to be created")] WidgetType widgetType, [Description("The color of the widget to be created")] WidgetColor widgetColor)
        {
            return new()
            {
                SerialNumber = $"{widgetType}-{widgetColor}-{Guid.NewGuid()}",
                Type = widgetType,
                Color = widgetColor
            };
        }
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetType
    {
        [Description("A widget that is useful.")]
        Useful,

        [Description("A widget that is decorative.")]
        Decorative
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetColor
    {
        [Description("Use when creating a red widget.")]
        Red,

        [Description("Use when creating a green widget.")]
        Green,

        [Description("Use when creating a blue widget.")]
        Blue
    }

    public class WidgetDetails
    {
        public string SerialNumber { get; init; }
        public WidgetType Type { get; init; }
        public WidgetColor Color { get; init; }
    }

    public Step2_Add_Plugins(ITestOutputHelper output) : base(output)
    {
    }
}
