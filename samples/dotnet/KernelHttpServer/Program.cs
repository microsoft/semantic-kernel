// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Memory;
using SqliteMemory;
using Microsoft.Data.Sqlite;

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
            .ConfigureServices(async services =>
            {
                //services.AddSingleton<IMemoryStore<float>>(new VolatileMemoryStore());

                //string databaseFile = "SKDataBase.db";
                //SqliteConnection.CreateFile("SKDataBase.db");
                SqliteConnection dbConnection = new SqliteConnection(@"Data Source=SKDataBase.db;");
                await dbConnection.OpenAsync(); // TODO: close connection when done (not sure where that code would reside)

                services.AddSingleton<IMemoryStore<float>>(new SqliteMemoryStore<float>(dbConnection));

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
