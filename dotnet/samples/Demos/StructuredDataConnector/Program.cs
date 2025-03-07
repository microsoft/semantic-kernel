// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

#pragma warning disable CA2007, VSTHRD111 // .ConfigureAwait(false)

namespace StructuredDataConnector;

internal sealed class Program
{
    internal static async Task Main(string[] args)
    {
        var serviceCollection = new ServiceCollection()
            .AddSingleton<IConfiguration>((sp) => new ConfigurationBuilder().AddUserSecrets<Program>().Build())
            .AddTransient<MyDbContext>()
            .AddTransient<StructuredDataService<MyDbContext>>();

        var serviceProvider = serviceCollection.BuildServiceProvider();
        using var structuredDataService = serviceProvider.GetRequiredService<StructuredDataService<MyDbContext>>();

        var dataBasePlugin = KernelPluginFactory.CreateFromFunctions("DatabasePlugin", "Allows CRUDE operations against the database",
            [
                structuredDataService.CreateSelectFunction<MyDbContext, MyEntity>(),
                structuredDataService.CreateInsertFunction<MyDbContext, MyEntity>(),
                structuredDataService.CreateUpdateFunction<MyDbContext, MyEntity>(),
                structuredDataService.CreateDeleteFunction<MyDbContext, MyEntity>(),
            ]
        );

        var kernel = new Kernel(serviceProvider, [dataBasePlugin]);

        var newRecord = new MyEntity
        {
            Description = $"New test - {Guid.NewGuid().ToString().Substring(0,4)}",
            DateCreated = DateTime.Now
        };

        // Direct calling the function
        var insertResult = await dataBasePlugin["InsertMyEntityRecord"].InvokeAsync(kernel, new() { ["entity"] = newRecord });
        var insertedEntity = insertResult.GetValue<MyEntity>()!;

        Console.WriteLine($"""
            ----- Inserted Record -----
            Id: {insertedEntity.Id}
            Description: {insertedEntity.Description}
            DateCreated: {insertedEntity.DateCreated}
            -----
            """);

        // Direct calling select function
        var selectResult = await dataBasePlugin["SelectMyEntityRecords"].InvokeAsync(kernel);
        var selectedEntities = selectResult.GetValue<IList<MyEntity>>()!;
        Console.WriteLine($"----- Selected {selectedEntities.Count} records -----");
        foreach (var entity in selectedEntities)
        {
            Console.WriteLine($"""
                Id: {entity.Id}
                Description: {entity.Description}
                -----
                """);
        }
    }

    private async Task UsingServiceDirectlyAsync<T>(StructuredDataService<T> structuredDataService)
        where T : DbContext
    {
        var result = structuredDataService.Select<MyEntity>();

        Console.WriteLine($"----- Records for {nameof(MyEntity)} -----");
        foreach (var entity in result)
        {
            Console.WriteLine($"""
                Id: {entity.Id}
                Description: {entity.Description}
                -----
                """);
        }

        var newRecord = new MyEntity
        {
            Description = "New test",
            DateCreated = DateTime.Now
        };

        var insertedEntity = await structuredDataService.InsertAsync(newRecord);
        Console.WriteLine($"""
            ----- Inserted Record -----
            Id: {insertedEntity.Id}
            Description: {insertedEntity.Description}
            DateCreated: {insertedEntity.DateCreated}
            -----
            """);
    }
}
