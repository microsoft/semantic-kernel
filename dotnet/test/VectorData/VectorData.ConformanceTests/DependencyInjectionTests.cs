// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorData.ConformanceTests;

public abstract class DependencyInjectionTests<TVectorStore, TCollection, TKey, TRecord>
    where TVectorStore : VectorStore
    where TCollection : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
{
    protected virtual string CollectionName => "collectionName";

    protected abstract void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null);

    public abstract IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates { get; }

    public abstract IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates { get; }

    [Fact]
    public void ServiceCollectionCantBeNull()
    {
        foreach (var registrationDelegate in this.StoreDelegates)
        {
            Assert.Throws<ArgumentNullException>(() => registrationDelegate(null!, null, ServiceLifetime.Singleton));
            Assert.Throws<ArgumentNullException>(() => registrationDelegate(null!, "serviceKey", ServiceLifetime.Singleton));
        }

        foreach (var registrationDelegate in this.CollectionDelegates)
        {
            Assert.Throws<ArgumentNullException>(() => registrationDelegate(null!, null, this.CollectionName, ServiceLifetime.Singleton));
            Assert.Throws<ArgumentNullException>(() => registrationDelegate(null!, "serviceKey", this.CollectionName, ServiceLifetime.Singleton));
        }
    }

    [Fact]
    public void CollectionNameCantBeNullOrEmpty()
    {
        const string EmptyCollectionName = "";

        foreach (var registrationDelegate in this.CollectionDelegates)
        {
            IServiceCollection services = this.CreateServices();

            Assert.Throws<ArgumentNullException>(() => registrationDelegate(services, null, null!, ServiceLifetime.Singleton));
            Assert.Throws<ArgumentNullException>(() => registrationDelegate(services, "serviceKey", null!, ServiceLifetime.Singleton));
            Assert.Throws<ArgumentException>(() => registrationDelegate(services, null, EmptyCollectionName, ServiceLifetime.Singleton));
            Assert.Throws<ArgumentException>(() => registrationDelegate(services, "serviceKey", EmptyCollectionName, ServiceLifetime.Singleton));
        }
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
        foreach (var registrationDelegate in this.StoreDelegates)
        {
            IServiceCollection services = this.CreateServices(serviceKey);

            registrationDelegate(services, serviceKey, lifetime);

            using ServiceProvider serviceProvider = services.BuildServiceProvider();
            // let's ensure that concrete types are registered
            Verify<TVectorStore>(serviceProvider, lifetime, serviceKey);
            // and the abstraction too
            Verify<VectorStore>(serviceProvider, lifetime, serviceKey);
        }
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public void CanRegisterCollections(ServiceLifetime lifetime, object? serviceKey)
    {
        foreach (var registrationDelegate in this.CollectionDelegates)
        {
            IServiceCollection services = this.CreateServices(serviceKey);

            registrationDelegate(services, serviceKey, this.CollectionName, lifetime);

            using ServiceProvider serviceProvider = services.BuildServiceProvider();
            // Let's ensure that concrete types are registered.
            Verify<TCollection>(serviceProvider, lifetime, serviceKey);
            // And the VectorStoreCollection abstraction.
            Verify<VectorStoreCollection<TKey, TRecord>>(serviceProvider, lifetime, serviceKey);
            // And the IVectorSearchable abstraction.
            Verify<IVectorSearchable<TRecord>>(serviceProvider, lifetime, serviceKey);

            if (typeof(IKeywordHybridSearchable<TRecord>).IsAssignableFrom(typeof(TCollection)))
            {
                Verify<IKeywordHybridSearchable<TRecord>>(serviceProvider, lifetime, serviceKey);
            }
            else
            {
                Assert.Null(serviceProvider.GetService<IKeywordHybridSearchable<TRecord>>());
            }
        }
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public virtual void CanRegisterConcreteTypeVectorStoreAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        foreach (var registrationDelegate in this.StoreDelegates)
        {
            IServiceCollection services = this.CreateServices(serviceKey);

            // Users may be willing to register more than one IVectorStore implementation.
            services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey, (sp, key) => new FakeVectorStore(), lifetime));

            registrationDelegate(services, serviceKey, lifetime);

            using ServiceProvider serviceProvider = services.BuildServiceProvider();
            // let's ensure that concrete types are registered
            Verify<TVectorStore>(serviceProvider, lifetime, serviceKey);
        }
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public void CanRegisterConcreteTypeCollectionsAfterSomeAbstractionHasBeenRegistered(ServiceLifetime lifetime, object? serviceKey)
    {
        foreach (var registrationDelegate in this.CollectionDelegates)
        {
            IServiceCollection services = this.CreateServices(serviceKey);

            // Users may be willing to register more than one VectorStoreCollection implementation.
            services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey, (sp, key) => new FakeVectorStoreRecordCollection(), lifetime));

            registrationDelegate(services, serviceKey, this.CollectionName, lifetime);

            using ServiceProvider serviceProvider = services.BuildServiceProvider();
            // let's ensure that concrete types are registered
            Verify<TCollection>(serviceProvider, lifetime, serviceKey);
        }
    }

    [Theory]
    [MemberData(nameof(LifetimesAndServiceKeys))]
    public void EmbeddingGeneratorIsResolved(ServiceLifetime lifetime, object? serviceKey)
    {
        foreach (var registrationDelegate in this.CollectionDelegates)
        {
            IServiceCollection services = this.CreateServices(serviceKey);

            bool wasResolved = false;
            services.AddSingleton<IEmbeddingGenerator>(sp =>
            {
                wasResolved = true;
                return null!;
            });

            registrationDelegate(services, serviceKey, this.CollectionName, lifetime);

            Assert.False(wasResolved); // it's lazy

            using ServiceProvider serviceProvider = services.BuildServiceProvider();
            using var collection = serviceKey is null
                ? serviceProvider.GetRequiredService<TCollection>()
                : serviceProvider.GetRequiredKeyedService<TCollection>(serviceKey);

            Assert.True(wasResolved);
        }
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
        public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override VectorStoreCollection<TKey1, TRecord1> GetCollection<TKey1, TRecord1>(string name, VectorStoreCollectionDefinition? definition = null) => throw new NotImplementedException();
        public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition? definition = null) => throw new NotImplementedException();
        public override object? GetService(Type serviceType, object? serviceKey = null) => throw new NotImplementedException();
        public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
    }

    private sealed class FakeVectorStoreRecordCollection : VectorStoreCollection<TKey, TRecord>
    {
        public override string Name => throw new NotImplementedException();
        public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override object? GetService(Type serviceType, object? serviceKey = null) => throw new NotImplementedException();
        public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(TInput searchValue, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default) => throw new NotImplementedException();
        public override Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default) => throw new NotImplementedException();
    }
}
