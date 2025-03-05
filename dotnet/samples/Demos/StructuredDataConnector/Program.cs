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
            AllowedTables = ["Test1"]
        };

        var result = structuredConnector.SearchByEntity<MyEntity>(e => e.Description == "Test");

        foreach (var entity in result)
        {
            Console.WriteLine($"Id: {entity.Id}, Description: {entity.Description}");
        }

        await foreach (var record in structuredConnector.SearchByTableAsync(structuredConnector.AllowedTables[0]).ConfigureAwait(false))
        {
            Console.WriteLine($"Id: {record[nameof(MyEntity.Id)]}, Description: {record[nameof(MyEntity.Description)]}");
        }
    }
}

internal sealed class MyDbContext : DbContext
{
    public MyDbContext(string connectionString)
        : base(connectionString)
    {
    }

    public DbSet<MyEntity>? MyEntities { get; set; }

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
