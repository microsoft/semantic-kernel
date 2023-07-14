// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql;

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using SemanticKernel.Data.Nl2Sql.Services;

internal static class Program
{
    public static string ConfigRoot { get; } = $@"{Repo.RootFolder}\samples\data\nl2sql\nl2sql.config";

    private static async Task Main(string[] args)
    {
        using var traceListener = new TextWriterTraceListener("nl2sql.log");

        var host =
            Host.CreateDefaultBuilder(args)
                .ConfigureAppConfiguration(
                    (context, config) =>
                    {
                        config
                            .AddJsonFile("appsettings.json")
                            .AddJsonFile($"appsettings.{context.HostingEnvironment.EnvironmentName}.json", optional: true);
                    })
                .ConfigureLogging(
                    (context, config) =>
                    {
                        config
                            .ClearProviders()
                            .AddConfiguration(context.Configuration.GetSection("Logging"))
                            .AddDebug()
                            .AddTraceSource(new SourceSwitch("FileTrace", $"{SourceLevels.Information}"), traceListener);
                    })
                .ConfigureServices(
                    (context, services) =>
                    {
                        services
                            .AddHostedService<Nl2SqlConsole>()
                            .AddSingleton(KernelFactory.Create(context.Configuration))
                            .AddSingleton(SqlConnectionProvider.Create(context.Configuration))
                            .AddSingleton(SchemaProvider.Create(context.Configuration));
                    })
             .UseConsoleLifetime()
             .Build();

        await host.RunAsync().ConfigureAwait(false);
    }
}
