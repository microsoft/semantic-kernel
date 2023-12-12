// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using RepoUtils;

/**
 * The following examples show how to use SK SDK in applications using DI/IoC containers.
 */
public static class Example40_DIContainer
{
    public static async Task RunAsync()
    {
        var collection = new ServiceCollection();
        collection.AddSingleton<ILoggerFactory>(ConsoleLogger.LoggerFactory);
        collection.AddOpenAITextGeneration(TestConfiguration.OpenAI.ModelId, TestConfiguration.OpenAI.ApiKey);
        collection.AddSingleton<Kernel>();

        // Registering class that uses Kernel to execute a plugin
        collection.AddTransient<KernelClient>();

        //Creating a service provider for resolving registered services
        var serviceProvider = collection.BuildServiceProvider();

        //If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the KernelClient class to a class that references it.
        //DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        var kernelClient = serviceProvider.GetRequiredService<KernelClient>();

        //Execute the function
        await kernelClient.SummarizeAsync("What's the tallest building in South America?");
    }

    /// <summary>
    /// Class that uses/references Kernel.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class KernelClient
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        private readonly Kernel _kernel;
        private readonly ILogger _logger;

        public KernelClient(Kernel kernel, ILoggerFactory loggerFactory)
        {
            this._kernel = kernel;
            this._logger = loggerFactory.CreateLogger(nameof(KernelClient));
        }

        public async Task SummarizeAsync(string ask)
        {
            string folder = RepoFiles.SamplePluginsPath();

            var summarizePlugin = this._kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

            var result = await this._kernel.InvokeAsync(summarizePlugin["Summarize"], new() { ["input"] = ask });

            this._logger.LogWarning("Result - {0}", result.GetValue<string>());
        }
    }
}
