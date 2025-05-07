// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
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
        IServiceCollection services = this.CreateServices();

        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(services, ServiceLifetime.Singleton, collectionName: null!, serviceKey: null));
        Assert.Throws<ArgumentNullException>(() => this.RegisterCollection(services, ServiceLifetime.Singleton, collectionName: null!, serviceKey: "notNull"));
        Assert.Throws<ArgumentException>(() => this.RegisterCollection(services, ServiceLifetime.Singleton, collectionName: "", serviceKey: null));
        Assert.Throws<ArgumentException>(() => this.RegisterCollection(services, ServiceLifetime.Singleton, collectionName: "", serviceKey: "notNull"));
    }

#pragma warning disable CA1000 // Do not declare static members on generic types
    public static IEnumerable<object?[]> LifetimesAndServiceKeys()
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
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public virtual void CanRegisterVectorStore(ServiceLifetime lifetime, object? serviceKey)
    {
        IServiceCollection services = this.CreateServices(serviceKey);

        this.RegisterVectorStore(services, lifetime, serviceKey);

        using ServiceProvider serviceProvider = services.BuildServiceProvider();
        // let's ensure that concrete types are registered
        Verify<TVectorStore>(serviceProvider, lifetime, serviceKey);
        // and the abstraction too
        Verify<VectorStore>(serviceProvider, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public void CanRegisterCollections(ServiceLifetime lifetime, object? serviceKey)
    {
        IServiceCollection services = this.CreateServices(serviceKey);

        this.RegisterCollection(services, lifetime, serviceKey: serviceKey);

        using ServiceProvider serviceProvider = services.BuildServiceProvider();
        // Let's ensure that concrete types are registered.
        Verify<TCollection>(serviceProvider, lifetime, serviceKey);
        // And the VectorStoreCollection abstraction.
        Verify<VectorStoreCollection<TKey, TRecord>>(serviceProvider, lifetime, serviceKey);
        // And the IVectorSearchable abstraction.
        Verify<IVectorSearchable<TRecord>>(serviceProvider, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public virtual void CanRegisterConcreteTypeVectorStoreAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        IServiceCollection services = this.CreateServices(serviceKey);

        // Users may be willing to register more than one IVectorStore implementation.
        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey, (sp, key) => new FakeVectorStore(), lifetime));

        this.RegisterVectorStore(services, lifetime, serviceKey);

        using ServiceProvider serviceProvider = services.BuildServiceProvider();
        // let's ensure that concrete types are registered
        Verify<TVectorStore>(serviceProvider, lifetime, serviceKey);
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public void CanRegisterConcreteTypeCollectionsAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        IServiceCollection services = this.CreateServices(serviceKey);

        // Users may be willing to register more than one VectorStoreCollection implementation.
        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey, (sp, key) => new FakeVectorStoreRecordCollection(), lifetime));

        this.RegisterCollection(services, lifetime, serviceKey: serviceKey);

        using ServiceProvider serviceProvider = services.BuildServiceProvider();
        // let's ensure that concrete types are registered
        Verify<TCollection>(serviceProvider, lifetime, serviceKey);
    }

    protected IServiceCollection CreateServices(object? serviceKey = null)
    {
        IServiceCollection services = new ServiceCollection();
#pragma warning disable CA2000 // Dispose objects before losing scope
        ConfigurationManager configuration = new();
#pragma warning restore CA2000 // Dispose objects before losing scope
        services.AddSingleton<IConfiguration>(configuration);

        this.PopulateConfiguration(configuration, serviceKey);

        return services;
    }

    private static void Verify<TService>(ServiceProvider serviceProvider, ServiceLifetime lifetime, object? serviceKey)
        where TService : class
    {
        TService? serviceFromFirstScope, serviceFromSecondScope, secondServiceFromSecondScope;

        using (IServiceScope scope1 = serviceProvider.CreateScope())
        {
            serviceFromFirstScope = Resolve<TService>(scope1.ServiceProvider, serviceKey);
        }

        using (IServiceScope scope2 = serviceProvider.CreateScope())
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
        public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
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
