// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using StructuredDataConnector.Abstractions;

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

        var result = structuredDataService.SearchByEntity<MyEntity>(e => e.Description == "Test");

        Console.WriteLine($"----- Records for {nameof(MyEntity)} -----");
        foreach (var entity in result)
        {
            Console.WriteLine($"""
                Id: {entity.Id}
                Description: {entity.Description}
                -----
                """);
        }
    }
}

internal sealed class MyDbContext : DbContext
{
    public MyDbContext(IConfiguration config) :
        base(config[$"ConnectionStrings:{nameof(MyDbContext)}"]!)
    {
    }

    public MyDbContext(string connectionString)
        : base(connectionString)
    {
    }

    protected override void OnModelCreating(DbModelBuilder modelBuilder)
    {
        Database.SetInitializer<MyDbContext>(null);
        modelBuilder.Entity<MyEntity>().ToTable("Test1");
        base.OnModelCreating(modelBuilder);
    }
}

internal sealed class MyEntity
{
    public Guid Id { get; set; }

    public string? Description { get; set; }

    public DateTime DateCreated { get; set; }
}
