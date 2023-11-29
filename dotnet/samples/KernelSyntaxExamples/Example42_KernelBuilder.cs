// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using new KernelBuilder().

#pragma warning disable CA1852

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example42_KernelBuilder
{
    public static Task RunAsync()
    {
        string azureOpenAIKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureOpenAIEndpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string azureOpenAIChatCompletionDeployment = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string azureOpenAIEmbeddingDeployment = TestConfiguration.AzureOpenAIEmbeddings.DeploymentName;

        // KernelBuilder provides a simple way to configure a Kernel. This constructs a kernel
        // with logging and an Azure OpenAI chat completion service configured.
        Kernel kernel1 = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey)
            .Build();

        // For greater flexibility and to incorporate arbitrary services, KernelBuilder.ConfigureServices
        // provides direct access to an underlying IServiceCollection. Multiple calls to ConfigureServices
        // may be made, each of which may register any number of services.
        Kernel kernel2 = new KernelBuilder()
            .ConfigureServices(c => c.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information)))
            .ConfigureServices(c =>
            {
                c.AddHttpClient();
                c.AddAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey);
            })
            .Build();

        // Plugins may also be configured via the corresponding ConfigurePlugins method. There are multiple
        // overloads of ConfigurePlugins, one of which provides access to the services registered with the
        // builder, such that a plugin can resolve and use those services.
        Kernel kernel3 = new KernelBuilder()
            .ConfigurePlugins((serviceProvider, plugins) =>
            {
                ILogger logger = serviceProvider.GetService<ILogger<KernelBuilder>>() ?? (ILogger)NullLogger.Instance;
                plugins.Add(new KernelPlugin("Example", new[]
                {
                    KernelFunctionFactory.CreateFromMethod(() => logger.LogInformation("Function invoked"), functionName: "LogInvocation")
                }));
            })
            .Build();

        // Every call to KernelBuilder.Build creates a new Kernel instance, with a new service provider
        // and a new plugin collection.
        var builder = new KernelBuilder();
        Debug.Assert(!ReferenceEquals(builder.Build(), builder.Build()));

        // KernelBuilder provides a convenient API for creating Kernel instances. However, it is just a
        // wrapper around a service collection and plugin collection, ultimately constructing a Kernel
        // using the public constructor that's available for anyone to use directly if desired.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddAzureOpenAIChatCompletion(azureOpenAIChatCompletionDeployment, azureOpenAIEndpoint, azureOpenAIKey);
        Kernel kernel4 = new(services.BuildServiceProvider());

        // Kernels can also be constructed and resolved via such a dependency injection container.
        services.AddTransient<Kernel>();
        Kernel kernel5 = services.BuildServiceProvider().GetRequiredService<Kernel>();

        return Task.CompletedTask;
    }
}
