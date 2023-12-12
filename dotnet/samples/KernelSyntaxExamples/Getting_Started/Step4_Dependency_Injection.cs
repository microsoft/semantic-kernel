// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once InconsistentNaming
// ReSharper disable once InconsistentNaming
using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using RepoUtils;

// ReSharper disable once InconsistentNaming
/**
* This example shows how to using Dependency Injection with the Semantic Kernel
*/
public static class Step4_Dependency_Injection
{
    /// <summary>
    /// Show how to create a <see cref="Kernel"/> that participates in Dependency Injection.
    /// </summary>
    public static async Task RunAsync()
    {
        // If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the KernelClient class to a class that references it.
        // DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        var serviceProvider = BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Invoke the kernel with a templated prompt and stream the results to the display
        KernelArguments arguments = new() { { "topic", "earth when viewed from space" } };
        await foreach (var update in kernel.InvokePromptStreamingAsync("What color is the {{$topic}}? Provide a detailed explanation.", arguments))
        {
            Console.Write(update);
        }
    }

    /// <summary>
    /// Build a ServiceProvdier that can be used to resolve services.
    /// </summary>
    private static ServiceProvider BuildServiceProvider()
    {
        var collection = new ServiceCollection();
        collection.AddSingleton<ILoggerFactory>(ConsoleLogger.LoggerFactory);

        var kernelBuilder = collection.AddKernel();
        kernelBuilder.Services.AddOpenAITextGeneration(TestConfiguration.OpenAI.ModelId, TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<TimeInformation>();

        return collection.BuildServiceProvider();
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation
    {
        private readonly ILogger _logger;

        public TimeInformation(ILoggerFactory loggerFactory)
        {
            this._logger = loggerFactory.CreateLogger(typeof(TimeInformation));
        }

        [KernelFunction]
        public string GetCurrentUtcTime()
        {
            var utcNow = DateTime.UtcNow.ToString("R");
            this._logger.LogInformation("Returning current time {0}", utcNow);
            return utcNow;
        }
    }
}
