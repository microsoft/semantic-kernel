// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.Extensions.Configuration;
using StructuredDataConnector.Abstractions;

namespace StructuredDataConnector;

internal sealed class Program
{
    internal static async Task Main(string[] args)
    {
        var _config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .Build();

        var connectionString = _config["ConnectionStrings:MyDbContext"]!;

        using var myDbContext = new MyDbContext(connectionString);
        using var structuredConnector = new StructuredDataService(myDbContext)
        {
            AllowedTables = ["Test1", "Test2"]
        };

        // Typed records query
        var result = structuredConnector.SearchByEntity<MyEntity>(e => e.Description == "Test");

        Console.WriteLine($"----- Records for {nameof(MyEntity)} -----");
        foreach (var entity in result)
        {
            Console.WriteLine($"""
                Id: {entity.Id}
                Description: {entity.Description}
                -----
                """);
        }

        // Abstract dictionary based records query
        await foreach (var record in structuredConnector
            .SearchByTableAsync(structuredConnector.AllowedTables[1])
            .ConfigureAwait(false))
        {
            Console.WriteLine($"----- Records for {structuredConnector.AllowedTables[1]} -----");
            foreach (var key in record.Keys)
            {
                Console.WriteLine($"{key}: {record[key]}");
            }
            Console.WriteLine($"-----");
        }
    }
}

internal sealed class MyDbContext : DbContext
{
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
