// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;
using Xunit.Abstractions;

namespace MistralAI;

/// <summary>
/// Demonstrates the use of function calling with MistralAI.
/// </summary>
public sealed class MistralAI_Function_Calling : BaseTest
{
    [Fact]
    public async Task GetChatMessageContentsAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddMistralChatCompletion(
                model: TestConfiguration.MistralAI.ChatModelId!,
                apiKey: TestConfiguration.MistralAI.ApiKey!);
        kernelBuilder.Plugins.AddFromType<WeatherPlugin>();
        Kernel kernel = kernelBuilder.Build();

        const string ChatPrompt = @"
            <message role=""system"">What is the weather like in Paris?</message>
        ";
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(
            ChatPrompt, new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions });
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        WriteLine(chatPromptResult);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
            ) => $"Weather in {location} is sunny and 18 celsius";
    }

    public MistralAI_Function_Calling(ITestOutputHelper output) : base(output) { }
}
