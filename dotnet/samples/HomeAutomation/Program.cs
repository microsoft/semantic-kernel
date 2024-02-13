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
        builder.Services.AddOptions<AzureOpenAiOptions>()
                        .Bind(builder.Configuration.GetSection(nameof(AzureOpenAiOptions)))
                        .ValidateDataAnnotations()
                        .ValidateOnStart();

        // Add plugins to include in all kernel instances here
        builder.Services.AddSingleton<IEnumerable<KernelPlugin>>(sp =>
        {
            return new KernelPlugin[]
            {
                KernelPluginFactory.CreateFromType<MyTimePlugin>(),
                KernelPluginFactory.CreateFromObject(new MyLightPlugin(turnedOn: false), "OfficeLight"),
                KernelPluginFactory.CreateFromObject(new MyLightPlugin(turnedOn: false), "PorchLight"),
            };
        });
        builder.Services.AddSingleton<KernelPluginCollection>();

        // Instantiate chat completion service that kernels will use
        builder.Services.AddSingleton<IChatCompletionService>(sp =>
        {
            AzureOpenAiOptions options = sp.GetRequiredService<IOptions<AzureOpenAiOptions>>().Value;

            return new AzureOpenAIChatCompletionService(options.Deployment, options.Endpoint, options.ApiKey);
        });

        // When created by the dependency injection container, Semantic Kernel logging is included by default
        builder.Services.AddTransient<Kernel>();

        using IHost host = builder.Build();

        await host.RunAsync();
    }
}
