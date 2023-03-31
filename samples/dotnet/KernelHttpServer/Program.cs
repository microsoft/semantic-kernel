// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Memory.Sqlite;
using Microsoft.Data.Sqlite;
using System.Data.Common;

namespace KernelHttpServer;

public static class Program
{
    public static void Main()
    {
        string dbName = "SKDataBase.db";
        SqliteConnection dbConnection = new SqliteConnection($@"Data Source={dbName};");

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
                //services.AddSingleton<IMemoryStore<float>>(new VolatileMemoryStore());

                services.AddSingleton<IMemoryStore<float>>(new SqliteMemoryStore<float>(dbConnection));

                // return JSON with expected lowercase naming
                services.Configure<JsonSerializerOptions>(options =>
                {
                    options.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
                });
            })
            .Build();

        host.Run();

        dbConnection.Dispose();
    }
}
