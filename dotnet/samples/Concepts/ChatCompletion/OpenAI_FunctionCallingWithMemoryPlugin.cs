// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;

namespace ChatCompletion;

/// <summary>
/// Samples show how to use <see cref="TextMemoryPlugin"/> with OpenAI chat completion.
/// </summary>
public class OpenAI_FunctionCallingWithMemoryPlugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample demonstrates how to use a function to retrieve useful information from the memory.
    /// </summary>
    /// <remarks>
    /// The old <see cref="VolatileMemoryStore"/> and <see cref="SemanticTextMemory"/> classes are used to store and retrieve information.
    /// These implementations will be replaced soon and this sample will be updated to demonstrate the new (much improved) pattern.
    /// </remarks>
    [Fact]
    public async Task UseFunctionCallingToRetrieveMemoriesAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        // Create a kernel with OpenAI chat completion and text embedding generation
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId!,
                apiKey: TestConfiguration.OpenAI.ApiKey!);
        kernelBuilder.AddOpenAIEmbeddingGenerator(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId!,
                apiKey: TestConfiguration.OpenAI.ApiKey!);
        kernelBuilder.Services.AddSingleton<ITestOutputHelper>(this.Output);
        kernelBuilder.Services.AddSingleton<IFunctionInvocationFilter, FunctionInvocationFilter>();
        Kernel kernel = kernelBuilder.Build();

        // Create a text memory store and populate it with sample data
        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        VolatileMemoryStore memoryStore = new();
        SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);
        string collectionName = "SemanticKernel";
        await PopulateMemoryAsync(collectionName, textMemory);

        // Add the text memory plugin to the kernel
        MemoryPlugin memoryPlugin = new(collectionName, textMemory);
        kernel.Plugins.AddFromObject(memoryPlugin, "Memory");

        // Invoke chat prompt with auto invocation of functions enabled
        var executionSettings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        var chatPrompt =
        """
            <message role="user">What is Semantic Kernel?</message>
        """;
        var response = await kernel.InvokePromptAsync(chatPrompt, new(executionSettings));

        Console.WriteLine(response);
    }

    #region private
    /// <summary>
    /// Utility to populate a text memory store with sample data.
    /// </summary>
    private static async Task PopulateMemoryAsync(string collection, SemanticTextMemory textMemory)
    {
        string[] entries =
        [
            "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions.",
            "Semantic Kernel is a new AI SDK, and a simple and yet powerful programming model that lets you add large language capabilities to your app in just a matter of minutes. It uses natural language prompting to create and execute semantic kernel AI tasks across multiple languages and platforms.",
            "In this guide, you learned how to quickly get started with Semantic Kernel by building a simple AI agent that can interact with an AI service and run your code. To see more examples and learn how to build more complex AI agents, check out our in-depth samples.",
            "The Semantic Kernel extension for Visual Studio Code makes it easy to design and test semantic functions.The extension provides an interface for designing semantic functions and allows you to test them with the push of a button with your existing models and data.",
            "The kernel is the central component of Semantic Kernel.At its simplest, the kernel is a Dependency Injection container that manages all of the services and plugins necessary to run your AI application."
        ];
        foreach (var entry in entries)
        {
            await textMemory.SaveInformationAsync(
                collection: collection,
                text: entry,
                id: Guid.NewGuid().ToString());
        }
    }

    /// <summary>
    /// Plugin that provides a function to retrieve useful information from the memory.
    /// </summary>
    private sealed class MemoryPlugin(string collection, ISemanticTextMemory memory)
    {
        [KernelFunction]
        [Description("Retrieve useful information to help answer a question.")]
        public async Task<string> GetUsefulInformationAsync(
            [Description("The question being asked")] string question)
        {
            List<MemoryQueryResult> memories = await memory
                .SearchAsync(collection, question)
                .ToListAsync()
                .ConfigureAwait(false);

            return JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
        }
    }

    /// <summary>
    /// Implementation of <see cref="IFunctionInvocationFilter"/> that logs the function invocation.
    /// </summary>
    private sealed class FunctionInvocationFilter(ITestOutputHelper output) : IFunctionInvocationFilter
    {
        private readonly ITestOutputHelper _output = output;

        /// <inheritdoc />
        public async Task OnFunctionInvocationAsync(Microsoft.SemanticKernel.FunctionInvocationContext context, Func<Microsoft.SemanticKernel.FunctionInvocationContext, Task> next)
        {
            this._output.WriteLine($"Function Invocation - {context.Function.Name}");
            await next(context);
        }
    }
    #endregion
}
