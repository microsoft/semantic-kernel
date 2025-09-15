// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace CosmosNoSql.ConformanceTests.DependencyInjection;

public class CosmosNoSqlDependencyInjectionTests
    : DependencyInjectionTests<CosmosNoSqlVectorStore, CosmosNoSqlCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    protected const string ConnectionString = "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=mock;";
    protected const string DatabaseName = "dbName";

    private static readonly CosmosClientOptions s_clientOptions = new()
    {
        UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default
    };

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("CosmosNoSql", serviceKey, "ConnectionString"), ConnectionString),
            new(CreateConfigKey("CosmosNoSql", serviceKey, "DatabaseName"), DatabaseName),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("CosmosNoSql:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("CosmosNoSql", serviceKey, "ConnectionString")).Value!;

    private static string DatabaseNameProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("CosmosNoSql:DatabaseName").Value!;

    private static string DatabaseNameProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("CosmosNoSql", serviceKey, "DatabaseName")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<CosmosClient>(sp => new CosmosClient(ConnectionString, s_clientOptions))
                    .AddSingleton<Database>(sp => sp.GetRequiredService<CosmosClient>().GetDatabase(DatabaseName))
                    .AddCosmosNoSqlCollection<SimpleRecord<string>>(name, lifetime: lifetime)
                : services
                    .AddSingleton<CosmosClient>(sp => new CosmosClient(ConnectionString, s_clientOptions))
                    .AddSingleton<Database>(sp => sp.GetRequiredService<CosmosClient>().GetDatabase(DatabaseName))
                    .AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
                    name, ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
                    serviceKey, name, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
                    name, ConnectionStringProvider, DatabaseNameProvider, lifetime: lifetime)
                : services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), sp => DatabaseNameProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddCosmosNoSqlVectorStore(
                    ConnectionString, DatabaseName, lifetime: lifetime)
                : services.AddKeyedCosmosNoSqlVectorStore(
                    serviceKey, ConnectionString, DatabaseName, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<CosmosClient>(sp => new CosmosClient(ConnectionString, s_clientOptions))
                    .AddSingleton<Database>(sp => sp.GetRequiredService<CosmosClient>().GetDatabase(DatabaseName))
                    .AddCosmosNoSqlVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<CosmosClient>(sp => new CosmosClient(ConnectionString, s_clientOptions))
                    .AddSingleton<Database>(sp => sp.GetRequiredService<CosmosClient>().GetDatabase(DatabaseName))
                    .AddKeyedCosmosNoSqlVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: null!, databaseNameProvider: DatabaseNameProvider));
    }

    [Fact]
    public void DatabaseNameProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionStringProvider: ConnectionStringProvider, databaseNameProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlVectorStore(connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlVectorStore(serviceKey: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", connectionString: "", DatabaseName));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: null!, DatabaseName));
        Assert.Throws<ArgumentException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: "", DatabaseName));
    }

    [Fact]
    public void DatabaseNameCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlVectorStore(ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlVectorStore(serviceKey: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddCosmosNoSqlCollection<SimpleRecord<string>>(
            name: "notNull", ConnectionString, databaseName: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedCosmosNoSqlCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", ConnectionString, databaseName: ""));
    }
}
