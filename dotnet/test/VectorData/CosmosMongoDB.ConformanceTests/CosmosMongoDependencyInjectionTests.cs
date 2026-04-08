// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using MongoDB.Driver;
using VectorData.ConformanceTests;
using Xunit;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoDependencyInjectionTests
    : DependencyInjectionTests<CosmosMongoVectorStore, CosmosMongoCollection<string, DependencyInjectionTests<string>.Record>, string, DependencyInjectionTests<string>.Record>
{
    protected const string ConnectionString = "mongodb://localhost:27017";
    protected const string DatabaseName = "dbName";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("CosmosMongo", serviceKey, "ConnectionString"), ConnectionString),
            new(CreateConfigKey("CosmosMongo", serviceKey, "DatabaseName"), DatabaseName),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("CosmosMongo:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("CosmosMongo", serviceKey, "ConnectionString")).Value!;

    private static string DatabaseNameProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("CosmosMongo:DatabaseName").Value!;

    private static string DatabaseNameProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("CosmosMongo", serviceKey, "DatabaseName")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddCosmosMongoCollection<Record>(name, lifetime: lifetime)
                : services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddKeyedCosmosMongoCollection<Record>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddCosmosMongoCollection<Record>(
                    name, ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedCosmosMongoCollection<Record>(
                    serviceKey, name, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddCosmosMongoCollection<Record>(
                    name, ConnectionStringProvider, DatabaseNameProvider, lifetime: lifetime)
                : services.AddKeyedCosmosMongoCollection<Record>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), sp => DatabaseNameProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddCosmosMongoVectorStore(
                    ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedCosmosMongoVectorStore(
                    serviceKey, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddCosmosMongoVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddKeyedCosmosMongoVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
    }

    [Fact]
    public void DatabaseNameProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoVectorStore(connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoVectorStore(serviceKey: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", connectionString: "", DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionString: "", DatabaseName));
    }

    [Fact]
    public void DatabaseNameCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoVectorStore(ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoVectorStore(serviceKey: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddCosmosMongoCollection<Record>(
            name: "notNull", ConnectionString, databaseName: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedCosmosMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: ""));
    }
}
