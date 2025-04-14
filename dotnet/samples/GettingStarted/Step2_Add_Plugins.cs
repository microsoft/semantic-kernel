// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json.Serialization;
using Microsoft.OpenApi.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace GettingStarted;

/// <summary>
/// This example shows how to load a <see cref="KernelPlugin"/> instances.
/// </summary>
public sealed class Step2_Add_Plugins(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows different ways to load a <see cref="KernelPlugin"/> instances.
    /// </summary>
    [Fact]
    public async Task AddPlugins()
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
        Console.WriteLine(await kernel.InvokePromptAsync("How many days until Christmas?"));

        // Example 2. Invoke the kernel with a templated prompt that invokes a plugin and display the result
        Console.WriteLine(await kernel.InvokePromptAsync("The current time is {{TimeInformation.GetCurrentUtcTime}}. How many days until Christmas?"));

        // Example 3. Invoke the kernel with a prompt and allow the AI to automatically invoke functions
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.", new(settings)));

        // Example 4. Invoke the kernel with a prompt and allow the AI to automatically invoke functions that use enumerations
        Console.WriteLine(await kernel.InvokePromptAsync("Create a handy lime colored widget for me.", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("Create a beautiful scarlet colored widget for me.", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("Create an attractive maroon and navy colored widget for me.", new(settings)));
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
    /// A plugin that creates widgets.
    /// </summary>
    public class WidgetFactory
    {
        [KernelFunction]
        [Description("Creates a new widget of the specified type and colors")]
        public WidgetDetails CreateWidget([Description("The type of widget to be created")] WidgetType widgetType, [Description("The colors of the widget to be created")] WidgetColor[] widgetColors)
        {
            var colors = string.Join('-', widgetColors.Select(c => c.GetDisplayName()).ToArray());
            return new()
            {
                SerialNumber = $"{widgetType}-{colors}-{Guid.NewGuid()}",
                Type = widgetType,
                Colors = widgetColors
            };
        }
    }

    /// <summary>
    /// A <see cref="JsonConverter"/> is required to correctly convert enum values.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetType
    {
        [Description("A widget that is useful.")]
        Useful,

        [Description("A widget that is decorative.")]
        Decorative
    }

    /// <summary>
    /// A <see cref="JsonConverter"/> is required to correctly convert enum values.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetColor
    {
        [Description("Use when creating a red item.")]
        Red,

        [Description("Use when creating a green item.")]
        Green,

        [Description("Use when creating a blue item.")]
        Blue
    }

    public class WidgetDetails
    {
        public string SerialNumber { get; init; }
        public WidgetType Type { get; init; }
        public WidgetColor[] Colors { get; init; }
    }
}
