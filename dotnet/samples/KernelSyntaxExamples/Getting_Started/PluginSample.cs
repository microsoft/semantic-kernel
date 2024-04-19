// Copyright (c) Microsoft. All rights reserved.

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
public sealed class PluginSample(ITestOutputHelper output) : BaseTest(output)
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
        kernelBuilder.Plugins.AddFromType<ConduitFactory>();
        Kernel kernel = kernelBuilder.Build();

        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions, ResponseFormat = "json_object" };
        WriteLine(await kernel.InvokePromptAsync("Create three and a half metres of round profile conduit. Return the conduit details in JSON format.", new(settings)));
    }

    /// <summary>
    /// A plugin that creates conduit.
    /// </summary>
    public class ConduitFactory
    {
        [KernelFunction]
        [Description("Creates conduit with the specified type and length")]
        public Conduit CreateWidget([Description("The type of conduit to be created")] ConduitType conduitType, [Description("The length of conduit to be created")] double length)
        {
            return new()
            {
                Type = conduitType,
                Length = length
            };
        }
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum ConduitType
    {
        [Description("A conduit that has a circular profile.")]
        Circular,

        [Description("A conduit that has a rectangular profile.")]
        Rectangular
    }

    public class Conduit
    {
        [Description("The conduit type. This will be either Rectangular or Circular.")]
        public ConduitType Type { get; init; }
        [Description("The length of the conduit measured in meters.")]
        public double Length { get; init; }
    }
}
