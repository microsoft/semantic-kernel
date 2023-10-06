// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Reliability.Basic;
using Microsoft.SemanticKernel.Services;

using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using RepoUtils;

/**
 * The following examples show how to use SK SDK in applications using DI/IoC containers.
 */
public static class Example40_DIContainer
{
    public static async Task RunAsync()
    {
        await UseKernelInDIPowerAppAsync();

        await UseKernelInDIPowerApp_AdvancedScenarioAsync();
    }

    /// <summary>
    /// This example shows how to register a Kernel in a DI container using KernelBuilder instead of
    /// registering its dependencies.
    /// </summary>
    private static async Task UseKernelInDIPowerAppAsync()
    {
        //Bootstrapping code that initializes the modules, components, and classes that applications use.
        //For regular .NET applications, the bootstrapping code usually resides either in the Main method or very close to it.
        //In ASP.NET Core applications, the bootstrapping code is typically located in the ConfigureServices method of the Startup class.

        //Registering Kernel dependencies
        var collection = new ServiceCollection();
        collection.AddTransient<ILoggerFactory>((_) => ConsoleLogger.LoggerFactory);

        //Registering Kernel
        collection.AddTransient<IKernel>((serviceProvider) =>
        {
            return Kernel.Builder
            .WithLoggerFactory(serviceProvider.GetRequiredService<ILoggerFactory>())
            .WithOpenAITextCompletionService(TestConfiguration.OpenAI.ModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();
        });

        //Registering class that uses Kernel to execute a plugin
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
    /// This example shows how to registered Kernel and all its dependencies in DI container.
    /// </summary>
    private static async Task UseKernelInDIPowerApp_AdvancedScenarioAsync()
    {
        //Bootstrapping code that initializes the modules, components, and classes that applications use.
        //For regular .NET applications, the bootstrapping code usually resides either in the Main method or very close to it.
        //In ASP.NET Core applications, the bootstrapping code is typically located in the ConfigureServices method of the Startup class.

        //Registering AI services Kernel is going to use
        var aiServicesCollection = new AIServiceCollection();
        aiServicesCollection.SetService<ITextCompletion>(() => new OpenAITextCompletion(TestConfiguration.OpenAI.ModelId, TestConfiguration.OpenAI.ApiKey));

        //Registering Kernel dependencies
        var collection = new ServiceCollection();
        collection.AddTransient<ILoggerFactory>((_) => ConsoleLogger.LoggerFactory);
        collection.AddTransient<IDelegatingHandlerFactory>((_) => BasicHttpRetryHandlerFactory.Instance);
        collection.AddTransient<IFunctionCollection, FunctionCollection>();
        collection.AddTransient<IPromptTemplateEngine, PromptTemplateEngine>();
        collection.AddTransient<ISemanticTextMemory>((_) => NullMemory.Instance);
        collection.AddTransient<IAIServiceProvider>((_) => aiServicesCollection.Build()); //Registering AI service provider that is used by Kernel to resolve AI services runtime

        //Registering Kernel
        collection.AddTransient<IKernel, Kernel>();

        //Registering class that uses Kernel to execute a plugin
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
        private readonly IKernel _kernel;
        private readonly ILogger _logger;

        public KernelClient(IKernel kernel, ILoggerFactory loggerFactory)
        {
            this._kernel = kernel;
            this._logger = loggerFactory.CreateLogger(nameof(KernelClient));
        }

        public async Task SummarizeAsync(string ask)
        {
            string folder = RepoFiles.SamplePluginsPath();

            var summarizeFunctions = this._kernel.ImportSemanticFunctionsFromDirectory(folder, "SummarizePlugin");

            var result = await this._kernel.RunAsync(ask, summarizeFunctions["Summarize"]);

            this._logger.LogWarning("Result - {0}", result.GetValue<string>());
        }
    }
}
