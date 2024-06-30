// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace DependencyInjection;

// The following examples show how to use SK SDK in applications using DI/IoC containers.
public class Kernel_Injecting(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        ServiceCollection collection = new();
        collection.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        collection.AddOpenAITextGeneration(TestConfiguration.OpenAI.ModelId, TestConfiguration.OpenAI.ApiKey);
        collection.AddSingleton<Kernel>();

        // Registering class that uses Kernel to execute a plugin
        collection.AddTransient<KernelClient>();

        // Create a service provider for resolving registered services
        await using ServiceProvider serviceProvider = collection.BuildServiceProvider();

        //If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the KernelClient class to a class that references it.
        //DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        KernelClient kernelClient = serviceProvider.GetRequiredService<KernelClient>();

        //Execute the function
        await kernelClient.SummarizeAsync("What's the tallest building in South America?");
    }

    /// <summary>
    /// Class that uses/references Kernel.
    /// </summary>
    private sealed class KernelClient(Kernel kernel, ILoggerFactory loggerFactory)
    {
        private readonly Kernel _kernel = kernel;
        private readonly ILogger _logger = loggerFactory.CreateLogger(nameof(KernelClient));

        public async Task SummarizeAsync(string ask)
        {
            string folder = RepoFiles.SamplePluginsPath();

            var summarizePlugin = this._kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

            var result = await this._kernel.InvokeAsync(summarizePlugin["Summarize"], new() { ["input"] = ask });

            this._logger.LogWarning("Result - {0}", result.GetValue<string>());
        }
    }
}
