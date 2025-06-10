// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerDependencyInjectionTests
    : DependencyInjectionTests<SqlServerVectorStore, SqlServerCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    protected const string ConnectionString = "Server=localhost;Database=master;Integrated Security=True;";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("SqlServer", serviceKey, "ConnectionString"), ConnectionString),
        ]);

    private static string ConnectionStringProvider(IServiceProvider sp)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection("SqlServer:ConnectionString").Value!;

    private static string ConnectionStringProvider(IServiceProvider sp, object serviceKey)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("SqlServer", serviceKey, "ConnectionString")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddSqlServerCollection<string, SimpleRecord<string>>(
                    name, connectionString: ConnectionString, lifetime: lifetime)
                : services.AddKeyedSqlServerCollection<string, SimpleRecord<string>>(
                    serviceKey, name, connectionString: ConnectionString, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddSqlServerCollection<string, SimpleRecord<string>>(
                    name, ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedSqlServerCollection<string, SimpleRecord<string>>(
                    serviceKey, name, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddSqlServerVectorStore(
                    ConnectionStringProvider, lifetime: lifetime)
                : services.AddKeyedSqlServerVectorStore(
                    serviceKey, sp => ConnectionStringProvider(sp, serviceKey), lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddSqlServerVectorStore(connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqlServerVectorStore(serviceKey: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddSqlServerCollection<string, SimpleRecord<string>>(name: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqlServerCollection<string, SimpleRecord<string>>(serviceKey: "notNull", name: "notNull", connectionStringProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddSqlServerCollection<string, SimpleRecord<string>>(
            name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddSqlServerCollection<string, SimpleRecord<string>>(
            name: "notNull", connectionString: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedSqlServerCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedSqlServerCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", connectionString: ""));
    }
}
