// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Memory;

namespace KernelHttpServer;

public static class Program
{
    public static void Main()
    {
        var host = new HostBuilder()
            .ConfigureFunctionsWorkerDefaults()
            .ConfigureAppConfiguration(configuration =>
            {
                var config = configuration.SetBasePath(Directory.GetCurrentDirectory())
                    .AddJsonFile("local.settings.json", optional: true, reloadOnChange: true);

                var builtConfig = config.Build();
            })
            .ConfigureServices(services =>
            {
                services.AddSingleton<IMemoryStore>(new VolatileMemoryStore());

                // return JSON with expected lowercase naming
                services.Configure<JsonSerializerOptions>(options =>
                {
                    options.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
                });
            })
            .Build();

        host.Run();
    }
}
