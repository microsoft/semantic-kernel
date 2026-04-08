// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using VectorData.ConformanceTests;
using Xunit;

namespace MongoDB.ConformanceTests;

public class MongoDependencyInjectionTests
    : DependencyInjectionTests<MongoVectorStore, MongoCollection<string, DependencyInjectionTests<string>.Record>, string, DependencyInjectionTests<string>.Record>
{
    protected const string ConnectionString = "mongodb://localhost:27017";
    protected const string DatabaseName = "dbName";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Mongo", serviceKey, "ConnectionString"), ConnectionString),
            new(CreateConfigKey("Mongo", serviceKey, "DatabaseName"), DatabaseName),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("Mongo:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Mongo", serviceKey, "ConnectionString")).Value!;

    private static string DatabaseNameProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("Mongo:DatabaseName").Value!;

    private static string DatabaseNameProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Mongo", serviceKey, "DatabaseName")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddMongoCollection<Record>(name, lifetime: lifetime)
                : services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddKeyedMongoCollection<Record>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddMongoCollection<Record>(
                    name, ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedMongoCollection<Record>(
                    serviceKey, name, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddMongoCollection<Record>(
                    name, ConnectionStringProvider, DatabaseNameProvider, lifetime: lifetime)
                : services.AddKeyedMongoCollection<Record>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), sp => DatabaseNameProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddMongoVectorStore(
                    ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedMongoVectorStore(
                    serviceKey, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddMongoVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<MongoClient>(sp => new MongoClient(MongoClientSettings.FromConnectionString(ConnectionString)))
                    .AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<MongoClient>().GetDatabase(DatabaseName))
                    .AddKeyedMongoVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddMongoCollection<Record>(
            name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
    }

    [Fact]
    public void DatabaseNameProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddMongoCollection<Record>(
            name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddMongoVectorStore(connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoVectorStore(serviceKey: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddMongoCollection<Record>(
            name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddMongoCollection<Record>(
            name: "notNull", connectionString: "", DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", connectionString: "", DatabaseName));
    }

    [Fact]
    public void DatabaseNameCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddMongoVectorStore(ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoVectorStore(serviceKey: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddMongoCollection<Record>(
            name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddMongoCollection<Record>(
            name: "notNull", ConnectionString, databaseName: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedMongoCollection<Record>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: ""));
    }
}
