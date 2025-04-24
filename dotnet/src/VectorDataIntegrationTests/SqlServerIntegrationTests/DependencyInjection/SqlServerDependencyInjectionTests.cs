// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorDataSpecificationTests.DependencyInjection;
using VectorDataSpecificationTests.Models;
using Xunit;

namespace SqlServerIntegrationTests.DependencyInjection;

public class SqlServerDependencyInjectionTests
    : DependencyInjectionTests<SqlServerVectorStore, SqlServerVectorStoreRecordCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    protected const string ConnectionString = "Server=localhost;Database=master;Integrated Security=True;";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("SqlServer", serviceKey, "ConnectionString"), ConnectionString),
        ]);

    protected override void RegisterVectorStore(IServiceCollection services, ServiceLifetime lifetime, object? serviceKey = null)
    {
        if (serviceKey is null)
        {
            services.AddSqlServerVectorStore(
                sp => sp.GetRequiredService<IConfiguration>().GetRequiredSection("SqlServer:ConnectionString").Value!,
                lifetime: lifetime);
        }
        else
        {
            services.AddKeyedSqlServerVectorStore(
                serviceKey,
                sp => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("SqlServer", serviceKey, "ConnectionString")).Value!,
                lifetime: lifetime);
        }
    }

    protected override void RegisterCollection(IServiceCollection services, ServiceLifetime lifetime, string collectionName = "name", object? serviceKey = null)
    {
        if (serviceKey is null)
        {
            services.AddSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
                collectionName,
                sp => sp.GetRequiredService<IConfiguration>().GetRequiredSection("SqlServer:ConnectionString").Value!,
                lifetime: lifetime);
        }
        else
        {
            services.AddKeyedSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
                serviceKey,
                collectionName,
                sp => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("SqlServer", serviceKey, "ConnectionString")).Value!,
                lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionStringProviderCantBeNull()
    {
        HostApplicationBuilder builder = this.CreateHostBuilder();

        Assert.Throws<ArgumentNullException>(() => builder.Services.AddSqlServerVectorStore(connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => builder.Services.AddKeyedSqlServerVectorStore(serviceKey: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => builder.Services.AddSqlServerVectorStoreCollection<string, SimpleRecord<string>>(collectionName: "notNull", connectionStringProvider: null!));
        Assert.Throws<ArgumentNullException>(() => builder.Services.AddKeyedSqlServerVectorStoreCollection<string, SimpleRecord<string>>(serviceKey: "notNull", collectionName: "notNull", connectionStringProvider: null!));
    }

    [Fact]
    public void ConnectionStringCantBeNullOrEmpty()
    {
        HostApplicationBuilder builder = this.CreateHostBuilder();

        Assert.Throws<ArgumentNullException>(() => builder.Services.AddSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
            collectionName: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => builder.Services.AddSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
            collectionName: "notNull", connectionString: ""));
        Assert.Throws<ArgumentNullException>(() => builder.Services.AddKeyedSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", collectionName: "notNull", connectionString: null!));
        Assert.Throws<ArgumentException>(() => builder.Services.AddKeyedSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
            serviceKey: "notNull", collectionName: "notNull", connectionString: ""));
    }
}

public class SqlServerDependencyInjectionTests_ConnectionStrings : SqlServerDependencyInjectionTests
{
    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
    {
        // do nothing, as in this scenario config should not be used at all
    }

    protected override void RegisterCollection(IServiceCollection services, ServiceLifetime lifetime, string collectionName = "name", object? serviceKey = null)
    {
        if (serviceKey is null)
        {
            services.AddSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
                collectionName,
                connectionString: ConnectionString,
                lifetime: lifetime);
        }
        else
        {
            services.AddKeyedSqlServerVectorStoreCollection<string, SimpleRecord<string>>(
                serviceKey,
                collectionName,
                connectionString: ConnectionString,
                lifetime: lifetime);
        }
    }

    public override void CanRegisterVectorStore(ServiceLifetime lifetime, object? serviceKey)
    {
        // do nothing, we don't provide a test for this scenario with raw connection string
    }

    public override void CanRegisterConcreteTypeVectorStoreAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        // do nothing, we don't provide a test for this scenario with raw connection string
    }
}
