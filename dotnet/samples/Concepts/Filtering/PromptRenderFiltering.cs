// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Filtering;

public class PromptRenderFiltering(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to use function and prompt filters in Kernel.
    /// </summary>
    [Fact]
    public async Task FunctionAndPromptFiltersAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<ITestOutputHelper>(this.Output);

        var kernel = builder.Build();

        // Add filter without DI
        kernel.PromptRenderFilters.Add(new FirstPromptFilter(this.Output));

        var function = kernel.CreateFunctionFromPrompt("What is Seattle", functionName: "MyFunction");
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", functions: [function]));
        var result = await kernel.InvokeAsync(kernel.Plugins["MyPlugin"]["MyFunction"]);

        Console.WriteLine(result);
    }

    [Fact]
    public async Task PromptFilterRenderedPromptOverrideAsync()
    {
        var builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IPromptRenderFilter, PromptFilterExample>();

        var kernel = builder.Build();

        var result = await kernel.InvokePromptAsync("Hi, how can you help me?");

        Console.WriteLine(result);

        // Output:
        // Prompt from filter
    }

    /// <summary>Shows syntax for prompt filter.</summary>
    private sealed class PromptFilterExample : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            // Example: get function information
            var functionName = context.Function.Name;

            await next(context);

            // Example: override rendered prompt before sending it to AI
            context.RenderedPrompt = "Respond with following text: Prompt from filter.";
        }
    }

    private sealed class FirstPromptFilter(ITestOutputHelper output) : IPromptRenderFilter
    {
        private readonly ITestOutputHelper _output = output;

        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.PromptRendering - {context.Function.PluginName}.{context.Function.Name}");
            await next(context);
            this._output.WriteLine($"{nameof(FirstPromptFilter)}.PromptRendered - {context.Function.PluginName}.{context.Function.Name}");
        }
    }
}
