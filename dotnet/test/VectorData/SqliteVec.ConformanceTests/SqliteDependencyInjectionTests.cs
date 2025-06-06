// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace SqliteVec.ConformanceTests;

public class SqliteDependencyInjectionTests
   : DependencyInjectionTests<SqliteVectorStore, SqliteCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    protected const string ConnectionString = "Data Source=:memory:";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Sqlite", serviceKey, "ConnectionString"), ConnectionString),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("Sqlite:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Sqlite", serviceKey, "ConnectionString")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddSqliteCollection<string, SimpleRecord<string>>(
                    name, connectionString: ConnectionString, lifetime: lifetime)
                : services.AddKeyedSqliteCollection<string, SimpleRecord<string>>(
                    serviceKey, name, connectionString: ConnectionString, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddSqliteCollection<string, SimpleRecord<string>>(
                    name, ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedSqliteCollection<string, SimpleRecord<string>>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddSqliteVectorStore(
                    ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedSqliteVectorStore(
                    serviceKey, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddSqliteVectorStore(connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqliteVectorStore(serviceKey: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddSqliteCollection<string, SimpleRecord<string>>(name: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqliteCollection<string, SimpleRecord<string>>(serviceKey: "notNull", name: "notNull", connectionStringProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddSqliteCollection<string, SimpleRecord<string>>(
            name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddSqliteCollection<string, SimpleRecord<string>>(
            name: "notNull", connectionString: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqliteCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedSqliteCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: ""));
    }
}
