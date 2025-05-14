// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.PgVector;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Models;
using Xunit;

namespace PostgresIntegrationTests.DependencyInjection;

public class PostgresDependencyInjectionTests
    : DependencyInjectionTests<PostgresVectorStore, PostgresCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    protected const string ConnectionString = "Host=localhost;Database=test;";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Postgres", serviceKey, "ConnectionString"), ConnectionString),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("Postgres:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Postgres", serviceKey, "ConnectionString")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, collectionName, lifetime) => serviceKey is null
                ? services.AddPostgresCollection<string, SimpleRecord<string>>(
                    collectionName, connectionString: ConnectionString, lifetime: lifetime)
                : services.AddKeyedPostgresCollection<string, SimpleRecord<string>>(
                    serviceKey, collectionName, connectionString: ConnectionString, lifetime: lifetime);

            yield return (services, serviceKey, collectionName, lifetime) => serviceKey is null
                ? services.AddPostgresCollection<string, SimpleRecord<string>>(
                    collectionName, ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedPostgresCollection<string, SimpleRecord<string>>(
                    serviceKey, collectionName, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddPostgresVectorStore(
                    ConnectionString, lifetime: lifetime)
                : services.AddKeyedPostgresVectorStore(
                    serviceKey, ConnectionString, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddPostgresVectorStore(
                    connectionStringProvider: ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedPostgresVectorStore(
                    serviceKey, connectionStringProvider: sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddPostgresCollection<string, SimpleRecord<string>>(collectionName: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresCollection<string, SimpleRecord<string>>(serviceKey: "notNull", collectionName: "notNull", connectionStringProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddPostgresVectorStore(connectionString: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresVectorStore(serviceKey: "notNull", connectionString: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddPostgresCollection<string, SimpleRecord<string>>(
            collectionName: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddPostgresCollection<string, SimpleRecord<string>>(
            collectionName: "notNull", connectionString: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", collectionName: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedPostgresCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", collectionName: "notNull", connectionString: ""));
    }
}
