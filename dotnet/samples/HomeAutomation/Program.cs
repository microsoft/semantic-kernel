/*
 Copyright (c) Microsoft. All rights reserved.

 Example application that uses Semantic Kernel.

 Loads app configuration from:
 - appsettings.json.
 - appsettings.{Environment}.json.
 - Secret Manager when the app runs in the "Development" environment (set through the DOTNET_ENVIRONMENT variable).
 - Environment variables.
 - Command-line arguments.
*/

using HomeAutomation.Options;
using HomeAutomation.Plugins;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace HomeAutomation;

internal static class Program
{
    internal static async Task Main(string[] args)
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

        // Actual code to execute is found in Worker class
        builder.Services.AddHostedService<Worker>();

        // Get configuration
        builder.Services.AddOptions<AzureOpenAI>()
                        .Bind(builder.Configuration.GetSection(nameof(AzureOpenAI)))
                        .ValidateDataAnnotations()
                        .ValidateOnStart();

        // Optionally set an HTTP retry policy
        builder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry 3 times
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.MaxRetryAttempts = 3;
                o.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(60);
            });
        });

        // Chat completion service that kernels will use
        builder.Services.AddSingleton<IChatCompletionService>(sp =>
        {
            AzureOpenAI options = sp.GetRequiredService<IOptions<AzureOpenAI>>().Value;

            // A custom HttpClient can be provided to this constructor
            return new AzureOpenAIChatCompletionService(options.ChatDeploymentName, options.Endpoint, options.ApiKey);
        });

        // Add plugins that can be used by kernels
        // The plugins are added as singletons so that they can be used by multiple kernels
        builder.Services.AddSingleton<MyTimePlugin>();
        builder.Services.AddKeyedSingleton<MyLightPlugin>("OfficeLight");
        builder.Services.AddKeyedSingleton<MyLightPlugin>("PorchLight", (sp, key) =>
        {
            return new MyLightPlugin(turnedOn: true);
        });

        // Add a home automation kernel to the dependency injection container
        builder.Services.AddKeyedTransient<Kernel>("HomeAutomationKernel", (sp, key) =>
        {
            // Create a collection of plugins that the kernel will use
            KernelPluginCollection pluginCollection = new();
            pluginCollection.AddFromObject(sp.GetRequiredService<MyTimePlugin>());
            pluginCollection.AddFromObject(sp.GetRequiredKeyedService<MyLightPlugin>("OfficeLight"), "OfficeLight");
            pluginCollection.AddFromObject(sp.GetRequiredKeyedService<MyLightPlugin>("PorchLight"), "PorchLight");

            return new Kernel(sp, pluginCollection);
        });

        // When created by the dependency injection container, Semantic Kernel logging is included by default
        //builder.Services.AddTransient<Kernel>();

        using IHost host = builder.Build();

        await host.RunAsync();
    }
}
