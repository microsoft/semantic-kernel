// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorDataSpecificationTests;

public abstract class DependencyInjectionTests<TVectorStore, TCollection, TKey, TRecord>
    where TVectorStore : VectorStore
    where TCollection : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
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
    public virtual void CanRegisterVectorStore(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        this.RegisterVectorStore(builder.Services, lifetime, serviceKey);

        using IHost host = builder.Build();
        // let's ensure that concrete types are registered
        Verify<TVectorStore>(host, lifetime, serviceKey);
        // and the abstraction too
        Verify<VectorStore>(host, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LiftetimesAndKeys))]
    public void CanRegisterCollections(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        this.RegisterCollection(builder.Services, lifetime, serviceKey: serviceKey);

        using IHost host = builder.Build();
        // Let's ensure that concrete types are registered.
        Verify<TCollection>(host, lifetime, serviceKey);
        // And the VectorStoreCollection abstraction.
        Verify<VectorStoreCollection<TKey, TRecord>>(host, lifetime, serviceKey);
        // And the IVectorSearchable abstraction.
        Verify<IVectorSearchable<TRecord>>(host, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LiftetimesAndKeys))]
    public virtual void CanRegisterConcreteTypeVectorStoreAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        // Users may be willing to register more than one IVectorStore implementation.
        if (serviceKey is null)
        {
            builder.Services.Add(new ServiceDescriptor(typeof(VectorStore), sp => new FakeVectorStore(), lifetime));
        }
        else
        {
            builder.Services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey, (sp, key) => new FakeVectorStore(), lifetime));
        }

        this.RegisterVectorStore(builder.Services, lifetime, serviceKey);

        using IHost host = builder.Build();
        // let's ensure that concrete types are registered
        Verify<TVectorStore>(host, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LiftetimesAndKeys))]
    public void CanRegisterConcreteTypeCollectionsAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        HostApplicationBuilder builder = this.CreateHostBuilder(serviceKey);

        // Users may be willing to register more than one VectorStoreCollection implementation.
        if (serviceKey is null)
        {
            builder.Services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), sp => new FakeVectorStoreRecordCollection(), lifetime));
        }
        else
        {
            builder.Services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey, (sp, key) => new FakeVectorStoreRecordCollection(), lifetime));
        }

        this.RegisterCollection(builder.Services, lifetime, serviceKey: serviceKey);

        using IHost host = builder.Build();
        // let's ensure that concrete types are registered
        Verify<TCollection>(host, lifetime, serviceKey);
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

    private sealed class FakeVectorStore : VectorStore
    {
        public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override VectorStoreCollection<TKey1, TRecord1> GetCollection<TKey1, TRecord1>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) => throw new NotImplementedException();
        public override object? GetService(Type serviceType, object? serviceKey = null) => throw new NotImplementedException();
        public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
    }

    private sealed class FakeVectorStoreRecordCollection : VectorStoreCollection<TKey, TRecord>
    {
        public override string Name => throw new NotImplementedException();
        public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task CreateCollectionAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task DeleteCollectionAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override object? GetService(Type serviceType, object? serviceKey = null) => throw new NotImplementedException();
        public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(TInput value, int top, RecordSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(TVector vector, int top, RecordSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default) => throw new NotImplementedException();
    }
}
