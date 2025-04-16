// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorDataSpecificationTests.DependencyInjection;

public abstract class DependencyInjectionTests<TKey, TRecord>
    where TKey : notnull
    where TRecord : notnull
{
    protected abstract void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null);

    protected abstract void RegisterVectorStore(IServiceCollection services, ServiceLifetime lifetime, object? serviceKey = null);

    protected abstract void RegisterCollection(IServiceCollection services, ServiceLifetime lifetime, string collectionName = "name", object? serviceKey = null);

    [Fact]
    public void ServiceCollectionCantBeNull()
    {
        Assert.Throws<ArgumentNullException>(() => this.RegisterVectorStore(null!, ServiceLifetime.Singleton, serviceKey: null));
        Assert.Throws<ArgumentNullException>(() => this.RegisterVectorStore(null!, ServiceLifetime.Singleton, serviceKey: "notNull"));
        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(null!, ServiceLifetime.Singleton, serviceKey: null));
        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(null!, ServiceLifetime.Singleton, serviceKey: "notNull"));
    }

    [Fact]
    public void CollectionNameCantBeNullOrEmpty()
    {
        HostApplicationBuilder builder = this.CreateHostBuilder();

        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(builder.Services, ServiceLifetime.Singleton, collectionName: null!, serviceKey: null));
        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(builder.Services, ServiceLifetime.Singleton, collectionName: null!, serviceKey: "notNull"));
        Assert.Throws<ArgumentException>(() => this.RegisterCollection(builder.Services, ServiceLifetime.Singleton, collectionName: "", serviceKey: null));
        Assert.Throws<ArgumentException>(() => this.RegisterCollection(builder.Services, ServiceLifetime.Singleton, collectionName: "", serviceKey: "notNull"));
    }

#pragma warning disable CA1000 // Do not declare static members on generic types
    public static IEnumerable<object?[]> LiftetimesAndKeys()
#pragma warning restore CA1000 // Do not declare static members on generic types
    {
        foreach (ServiceLifetime lifetime in new ServiceLifetime[] { ServiceLifetime.Scoped, ServiceLifetime.Singleton, ServiceLifetime.Transient })
        {
            yield return new object?[] { lifetime, null };
            yield return new object?[] { lifetime, "key" };
            yield return new object?[] { lifetime, 8 };
        }
    }

    [Theory]
    [MemberData(nameof(LiftetimesAndKeys))]
    public void CanRegisterVectorStore(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        this.RegisterVectorStore(builder.Services, lifetime, serviceKey);

        using IHost host = builder.Build();
        Verify<IVectorStore>(host, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LiftetimesAndKeys))]
    public void CanRegisterCollections(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        this.RegisterCollection(builder.Services, lifetime, serviceKey: serviceKey);

        using IHost host = builder.Build();
        Verify<IVectorStoreRecordCollection<TKey, TRecord>>(host, lifetime, serviceKey);
    }

    protected HostApplicationBuilder CreateHostBuilder(object? serviceKey = null)
    {
        HostApplicationBuilder builder = Host.CreateEmptyApplicationBuilder(settings: null);

        this.PopulateConfiguration(builder.Configuration, serviceKey);

        return builder;
    }

    private static void Verify<TService>(IHost host, ServiceLifetime lifetime, object? serviceKey)
        where TService : class
    {
        TService? serviceFromFirstScope, serviceFromSecondScope, secondServiceFromSecondScope;

        using (IServiceScope scope1 = host.Services.CreateScope())
        {
            serviceFromFirstScope = Resolve<TService>(scope1.ServiceProvider, serviceKey);
        }

        using (IServiceScope scope2 = host.Services.CreateScope())
        {
            serviceFromSecondScope = Resolve<TService>(scope2.ServiceProvider, serviceKey);

            secondServiceFromSecondScope = Resolve<TService>(scope2.ServiceProvider, serviceKey);
        }

        Assert.NotNull(serviceFromFirstScope);
        Assert.NotNull(serviceFromSecondScope);
        Assert.NotNull(secondServiceFromSecondScope);

        switch (lifetime)
        {
            case ServiceLifetime.Singleton:
                Assert.Same(serviceFromFirstScope, serviceFromSecondScope);
                Assert.Same(serviceFromSecondScope, secondServiceFromSecondScope);
                break;
            case ServiceLifetime.Scoped:
                Assert.NotSame(serviceFromFirstScope, serviceFromSecondScope);
                Assert.Same(serviceFromSecondScope, secondServiceFromSecondScope);
                break;
            case ServiceLifetime.Transient:
                Assert.NotSame(serviceFromFirstScope, serviceFromSecondScope);
                Assert.NotSame(serviceFromSecondScope, secondServiceFromSecondScope);
                break;
        }
    }

    protected static string CreateConfigKey(string prefix, object? serviceKey, string suffix)
        => serviceKey is null ? $"{prefix}:{suffix}" : $"{prefix}:{serviceKey}:{suffix}";

    private static TService Resolve<TService>(IServiceProvider serviceProvider, object? serviceKey = null) where TService : notnull
        => serviceKey is null
            ? serviceProvider.GetRequiredService<TService>()
            : serviceProvider.GetRequiredKeyedService<TService>(serviceKey);
}
