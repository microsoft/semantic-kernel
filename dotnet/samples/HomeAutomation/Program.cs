/*
 Copyright (c) Microsoft. All rights reserved.

 Example that demonstrates how to use Semantic Kernel in conjunction with dependency injection.

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
        builder.Services.AddOptions<AzureOpenAI>()
                        .Bind(builder.Configuration.GetSection(nameof(AzureOpenAI)))
                        .ValidateDataAnnotations()
                        .ValidateOnStart();

        // Chat completion service that kernels will use
        builder.Services.AddSingleton<IChatCompletionService>(sp =>
        {
            AzureOpenAI options = sp.GetRequiredService<IOptions<AzureOpenAI>>().Value;

            // A custom HttpClient can be provided to this constructor
            return new AzureOpenAIChatCompletionService(options.ChatDeploymentName, options.Endpoint, options.ApiKey);

            /* Alternatively, you can use plain, non-Azure OpenAI after loading OpenAIOptions instead
               of AzureOpenAI options with builder.Services.AddOptions:
            OpenAI options = sp.GetRequiredService<IOptions<OpenAIOptions>>().Value;

            return new OpenAIChatCompletionService(options.ChatModelId, options.ApiKey);*/
        });

        // Add plugins that can be used by kernels
        // The plugins are added as singletons so that they can be used by multiple kernels
        builder.Services.AddSingleton<MyTimePlugin>();
        builder.Services.AddSingleton<MyAlarmPlugin>();
        builder.Services.AddKeyedSingleton<MyLightPlugin>("OfficeLight");
        builder.Services.AddKeyedSingleton<MyLightPlugin>("PorchLight", (sp, key) =>
        {
            return new MyLightPlugin(turnedOn: true);
        });

        /* To add an OpenAI or OpenAPI plugin, you need to be using Microsoft.SemanticKernel.Plugins.OpenApi.
           Then create a temporary kernel, use it to load the plugin and add it as keyed singleton.
        Kernel kernel = new();
        KernelPlugin openAIPlugin = await kernel.ImportPluginFromOpenAIAsync("<plugin name>", new Uri("<OpenAI-plugin>"));
        builder.Services.AddKeyedSingleton<KernelPlugin>("MyImportedOpenAIPlugin", openAIPlugin);

        KernelPlugin openApiPlugin = await kernel.ImportPluginFromOpenApiAsync("<plugin name>", new Uri("<OpenAPI-plugin>"));
        builder.Services.AddKeyedSingleton<KernelPlugin>("MyImportedOpenApiPlugin", openApiPlugin);*/

        // Add a home automation kernel to the dependency injection container
        builder.Services.AddKeyedTransient<Kernel>("HomeAutomationKernel", (sp, key) =>
        {
            // Create a collection of plugins that the kernel will use
            KernelPluginCollection pluginCollection = new();
            pluginCollection.AddFromObject(sp.GetRequiredService<MyTimePlugin>());
            pluginCollection.AddFromObject(sp.GetRequiredService<MyAlarmPlugin>());
            pluginCollection.AddFromObject(sp.GetRequiredKeyedService<MyLightPlugin>("OfficeLight"), "OfficeLight");
            pluginCollection.AddFromObject(sp.GetRequiredKeyedService<MyLightPlugin>("PorchLight"), "PorchLight");

            // When created by the dependency injection container, Semantic Kernel logging is included by default
            return new Kernel(sp, pluginCollection);
        });

        using IHost host = builder.Build();

        await host.RunAsync();
    }
}
