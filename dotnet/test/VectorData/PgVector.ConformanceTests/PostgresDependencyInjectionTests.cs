// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.PgVector;
using VectorData.ConformanceTests;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresDependencyInjectionTests
    : DependencyInjectionTests<PostgresVectorStore, PostgresCollection<string, DependencyInjectionTests<string>.Record>, string, DependencyInjectionTests<string>.Record>
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
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddPostgresCollection<string, Record>(
                    name, connectionString: ConnectionString, lifetime: lifetime)
                : services.AddKeyedPostgresCollection<string, Record>(
                    serviceKey, name, connectionString: ConnectionString, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddPostgresCollection<string, Record>(
                    name, ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedPostgresCollection<string, Record>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
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

        Assert.Throws<ArgumentNullException>(() => services.AddPostgresCollection<string, Record>(name: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresCollection<string, Record>(serviceKey: "notNull", name: "notNull", connectionStringProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddPostgresVectorStore(connectionString: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresVectorStore(serviceKey: "notNull", connectionString: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddPostgresCollection<string, Record>(
            name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddPostgresCollection<string, Record>(
            name: "notNull", connectionString: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPostgresCollection<string, Record>(
            serviceKey: "notNull", name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedPostgresCollection<string, Record>(
            serviceKey: "notNull", name: "notNull", connectionString: ""));
    }
}
