// Copyright (c) Microsoft. All rights reserved.

using AIPlugins.AzureFunctions;
using AIPlugins.AzureFunctions.Extensions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        services
            .AddSingleton<IKernelFactory, KernelFactory>()
            .AddTransient<IAIPluginRunner, KernelAIPluginRunner>();
    })
    .Build();

host.Run();
