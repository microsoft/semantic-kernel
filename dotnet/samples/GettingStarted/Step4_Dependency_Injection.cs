﻿// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace GettingStarted;

/// <summary>
/// This example shows how to using Dependency Injection with the Semantic Kernel
/// </summary>
public sealed class Step4_Dependency_Injection(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="Kernel"/> that participates in Dependency Injection.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the KernelClient class to a class that references it.
        // DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        var serviceProvider = BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Invoke the kernel with a templated prompt and stream the results to the display
        KernelArguments arguments = new() { { "topic", "earth when viewed from space" } };
        await foreach (var update in
                       kernel.InvokePromptStreamingAsync("What color is the {{$topic}}? Provide a detailed explanation.", arguments))
        {
            Console.Write(update);
        }
    }

    /// <summary>
    /// Build a ServiceProvider that can be used to resolve services.
    /// </summary>
    private ServiceProvider BuildServiceProvider()
    {
        var collection = new ServiceCollection();
        collection.AddSingleton<ILoggerFactory>(new XunitLogger(this.Output));

        var kernelBuilder = collection.AddKernel();
        kernelBuilder.Services.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<TimeInformation>();

        return collection.BuildServiceProvider();
    }

    /// <summary>
    /// A plugin that returns the current time.
    /// </summary>
    public class TimeInformation(ILoggerFactory loggerFactory)
    {
        private readonly ILogger _logger = loggerFactory.CreateLogger(typeof(TimeInformation));

        [KernelFunction]
        [Description("Retrieves the current time in UTC.")]
        public string GetCurrentUtcTime()
        {
            var utcNow = DateTime.UtcNow.ToString("R");
            this._logger.LogInformation("Returning current time {0}", utcNow);
            return utcNow;
        }
    }
}
