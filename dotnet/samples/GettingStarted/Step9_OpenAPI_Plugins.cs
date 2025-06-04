// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Resources;

namespace GettingStarted;

/// <summary>
/// This example shows how to load an Open API <see cref="KernelPlugin"/> instance.
/// </summary>
public sealed class Step9_OpenAPI_Plugins(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to load an Open API <see cref="KernelPlugin"/> instance.
    /// </summary>
    [Fact]
    public async Task AddOpenAPIPlugins()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Load OpenAPI plugin
        var stream = EmbeddedResource.ReadStream("repair-service.json");
        var plugin = await kernel.ImportPluginFromOpenApiAsync("RepairService", stream!);

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("List all of the repairs .", new(settings)));
    }

    /// <summary>
    /// Shows how to transform an Open API <see cref="KernelPlugin"/> instance to support dependency injection.
    /// </summary>
    [Fact]
    public async Task TransformOpenAPIPlugins()
    {
        // Create a kernel with OpenAI chat completion
        var serviceProvider = BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Load OpenAPI plugin
        var stream = EmbeddedResource.ReadStream("repair-service.json");
        var plugin = await kernel.CreatePluginFromOpenApiAsync("RepairService", stream!);

        // Transform the plugin to use IMechanicService via dependency injection
        kernel.Plugins.Add(TransformPlugin(plugin));

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("Book an appointment to drain the old engine oil and replace it with fresh oil.", new(settings)));
    }

    /// <summary>
    /// Build a ServiceProvider that can be used to resolve services.
    /// </summary>
    private ServiceProvider BuildServiceProvider()
    {
        var collection = new ServiceCollection();
        collection.AddSingleton<IMechanicService>(new FakeMechanicService());

        var kernelBuilder = collection.AddKernel();
        kernelBuilder.Services.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        return collection.BuildServiceProvider();
    }

    /// <summary>
    /// Transform the plugin to change the behavior of the createRepair function.
    /// </summary>
    public static KernelPlugin TransformPlugin(KernelPlugin plugin)
    {
        List<KernelFunction>? functions = [];

        foreach (KernelFunction function in plugin)
        {
            if (function.Name == "createRepair")
            {
                functions.Add(CreateRepairFunction(function));
            }
            else
            {
                functions.Add(function);
            }
        }

        return KernelPluginFactory.CreateFromFunctions(plugin.Name, plugin.Description, functions);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> instance for the createRepair operation which only takes
    /// the title, description parameters and has a delegate which uses the IMechanicService to get the
    /// assignedTo.
    /// </summary>
    private static KernelFunction CreateRepairFunction(KernelFunction function)
    {
        var method = (
            Kernel kernel,
            KernelFunction currentFunction,
            KernelArguments arguments,
            [FromKernelServices] IMechanicService mechanicService,
            CancellationToken cancellationToken) =>
        {
            arguments.Add("assignedTo", mechanicService.GetMechanic());
            arguments.Add("date", DateTime.UtcNow.ToString("R"));

            return function.InvokeAsync(kernel, arguments, cancellationToken);
        };

        var options = new KernelFunctionFromMethodOptions()
        {
            FunctionName = function.Name,
            Description = function.Description,
            Parameters = function.Metadata.Parameters.Where(p => p.Name == "title" || p.Name == "description").ToList(),
            ReturnParameter = function.Metadata.ReturnParameter,
        };

        return KernelFunctionFactory.CreateFromMethod(method, options);
    }

    /// <summary>
    /// Interface for a service to get the mechanic to assign to the next job.
    /// </summary>
    public interface IMechanicService
    {
        /// <summary>
        /// Return the name of the mechanic to assign the next job to.
        /// </summary>
        string GetMechanic();
    }

    /// <summary>
    /// Fake implementation of <see cref="IMechanicService"/>
    /// </summary>
    public class FakeMechanicService : IMechanicService
    {
        /// <inheritdoc/>
        public string GetMechanic() => "Bob";
    }
}
