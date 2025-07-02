// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Xunit;

namespace VectorData.UnitTests;

#pragma warning disable CA2000 // Dispose objects before losing scope

public class CollectionModelBuilderTests
{
    [Fact]
    public void Default_embedding_generator_without_record_definition()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();
        var model = new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), definition: null, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(Embedding<float>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_clr_type_and_record_definition()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<Half>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    // The following configures the property to be Embedding<Half> (non-default embedding type for this connector)
                    EmbeddingType = typeof(Embedding<Half>)
                }
            ]
        };

        var model = new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), recordDefinition, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(Embedding<Half>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_dynamic()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
            ]
        };

        var model = new CustomModelBuilder().BuildDynamic(recordDefinition, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(Embedding<float>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_dynamic_and_non_default_EmbeddingType()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<Half>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingType = typeof(Embedding<Half>)
                }
            ]
        };

        var model = new CustomModelBuilder().BuildDynamic(recordDefinition, embeddingGenerator);

        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(Embedding<Half>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Property_embedding_generator_takes_precedence_over_default_generator()
    {
        using var propertyEmbeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();
        using var defaultEmbeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingGenerator = propertyEmbeddingGenerator
                }
            ]
        };

        var model = new CustomModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator);

        Assert.Same(propertyEmbeddingGenerator, model.VectorProperty.EmbeddingGenerator);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Embedding_property_type_with_default_embedding_generator(bool dynamic)
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var model = dynamic
            ? new CustomModelBuilder().BuildDynamic(
                new VectorStoreCollectionDefinition
                {
                    Properties =
                    [
                        new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                        new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                        new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(ReadOnlyMemory<float>), dimensions: 3)
                    ]
                },
                embeddingGenerator)
            : new CustomModelBuilder().Build(typeof(RecordWithEmbeddingVectorProperty), definition: null, embeddingGenerator);

        var vectorProperty = model.VectorProperty;
        Assert.Same(embeddingGenerator, vectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(ReadOnlyMemory<float>), vectorProperty.Type);
    }

    [Fact]
    public void Embedding_property_type_with_property_embedding_generator()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<int, Embedding<float>>();

        var model = new CustomModelBuilder().Build(
            typeof(RecordWithEmbeddingVectorProperty),
            new VectorStoreCollectionDefinition
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                    new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                    new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(ReadOnlyMemory<float>), dimensions: 3)
                    {
                        EmbeddingGenerator = embeddingGenerator
                    }
                ]
            },
            embeddingGenerator);

        var vectorProperty = model.VectorProperty;
        Assert.Same(embeddingGenerator, vectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(ReadOnlyMemory<float>), vectorProperty.EmbeddingType);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Custom_input_type(bool dynamic)
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<Customer, Embedding<float>>();

        // TODO: Allow custom input type without a record definition (i.e. generic attribute)
        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty<Customer>(nameof(RecordWithEmbeddingVectorProperty.Embedding), dimensions: 3)
            ]
        };

        var model = dynamic
            ? new CustomModelBuilder().BuildDynamic(recordDefinition, embeddingGenerator)
            : new CustomModelBuilder().Build(typeof(RecordWithCustomerVectorProperty), recordDefinition, embeddingGenerator);

        var vectorProperty = model.VectorProperty;

        Assert.Same(embeddingGenerator, vectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(Customer), vectorProperty.Type);
        Assert.Same(typeof(Embedding<float>), vectorProperty.EmbeddingType);
    }

    [Fact]
    public void Incompatible_embedding_on_embedding_generator_throws()
    {
        // Embedding<long> is not a supported embedding type by the connector
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<long>>();

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), definition: null, embeddingGenerator));

        Assert.Equal($"Embedding generator 'FakeEmbeddingGenerator<string, Embedding<long>>' on vector property '{nameof(RecordWithStringVectorProperty.Embedding)}' cannot convert the input type 'string' to a supported vector type (one of: ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<Half>, Embedding<Half>, Half[]).", exception.Message);
    }

    [Fact]
    public void Incompatible_input_on_embedding_generator_throws()
    {
        // int is not a supported input type for the embedding generator
        using var embeddingGenerator = new FakeEmbeddingGenerator<int, Embedding<float>>();

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), definition: null, embeddingGenerator));

        Assert.Equal($"Embedding generator 'FakeEmbeddingGenerator<int, Embedding<float>>' on vector property '{nameof(RecordWithStringVectorProperty.Embedding)}' cannot convert the input type 'string' to a supported vector type (one of: ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<Half>, Embedding<Half>, Half[]).", exception.Message);
    }

    [Fact]
    public void Non_embedding_vector_property_without_embedding_generator_throws()
    {
        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), definition: null, defaultEmbeddingGenerator: null));

        Assert.Equal($"Vector property '{nameof(RecordWithStringVectorProperty.Embedding)}' has type 'string' which isn't supported by your provider, and no embedding generator is configured. Configure a generator that supports converting 'string' to vector type supported by your provider.", exception.Message);
    }

    [Fact]
    public void EmbeddingType_not_supported_by_provider()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<Half>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingType = typeof(Embedding<byte>) // The provider supports float/Half only, not byte
                }
            ]
        };

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), recordDefinition, embeddingGenerator));

        Assert.Equal("Vector property 'Embedding' has embedding type 'Embedding<Byte>' configured, but that type isn't supported by your provider. Supported types are ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<Half>, Embedding<Half>, Half[].", exception.Message);
    }

    [Fact]
    public void EmbeddingType_not_supported_by_generator()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingType = typeof(Embedding<Half>) // The generator (instantiated above) supports only Embedding<float>
                }
            ]
        };

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), recordDefinition, embeddingGenerator));

        Assert.Equal("Vector property 'Embedding' has embedding type 'Embedding<Half>' configured, but that type isn't supported by your embedding generator.", exception.Message);
    }

    [Fact]
    public void Missing_Type_on_property_definition()
    {
        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(ReadOnlyMemory<float>), dimensions: 3)
            ]
        };

        // Key
        recordDefinition.Properties[0].Type = null;
        var exception = Assert.Throws<InvalidOperationException>(() => new CustomModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null));
        Assert.Equal($"Property '{nameof(RecordWithEmbeddingVectorProperty.Id)}' has no type specified in its definition, and does not have a corresponding .NET property. Specify the type on the definition.", exception.Message);

        // Data
        recordDefinition.Properties[0].Type = typeof(int);
        recordDefinition.Properties[1].Type = null;
        exception = Assert.Throws<InvalidOperationException>(() => new CustomModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null));
        Assert.Equal($"Property '{nameof(RecordWithEmbeddingVectorProperty.Name)}' has no type specified in its definition, and does not have a corresponding .NET property. Specify the type on the definition.", exception.Message);

        // Vector
        recordDefinition.Properties[1].Type = typeof(string);
        recordDefinition.Properties[2].Type = null;
        exception = Assert.Throws<InvalidOperationException>(() => new CustomModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null));
        Assert.Equal($"Property '{nameof(RecordWithEmbeddingVectorProperty.Embedding)}' has no type specified in its definition, and does not have a corresponding .NET property. Specify the type on the definition.", exception.Message);
    }

    public class RecordWithStringVectorProperty
    {
        [VectorStoreKey]
        public int Id { get; set; }

        [VectorStoreData]
        public string Name { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public string Embedding { get; set; }
    }

    public class RecordWithEmbeddingVectorProperty
    {
        [VectorStoreKey]
        public int Id { get; set; }

        [VectorStoreData]
        public string Name { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    public class RecordWithCustomerVectorProperty
    {
        [VectorStoreKey]
        public int Id { get; set; }

        [VectorStoreData]
        public string Name { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public Customer Embedding { get; set; }
    }

    public class Customer
    {
        public string FirstName { get; set; }
        public string LastName { get; set; }
    }

    private sealed class CustomModelBuilder(CollectionModelBuildingOptions? options = null)
        : CollectionModelBuilder(options ?? s_defaultOptions)
    {
        private static readonly CollectionModelBuildingOptions s_defaultOptions = new()
        {
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true,
            RequiresAtLeastOneVector = false
        };

        protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        {
            supportedTypes = "string, int";

            return type == typeof(string) || type == typeof(int);
        }

        protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        {
            supportedTypes = "string, int";

            if (Nullable.GetUnderlyingType(type) is Type underlyingType)
            {
                type = underlyingType;
            }

            return type == typeof(string) || type == typeof(int);
        }

        protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
            => IsVectorPropertyTypeValidCore(type, out supportedTypes);

        internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
        {
            supportedTypes = "ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<Half>, Embedding<Half>, Half[]";

            if (Nullable.GetUnderlyingType(type) is Type underlyingType)
            {
                type = underlyingType;
            }

            return type == typeof(ReadOnlyMemory<float>)
                || type == typeof(Embedding<float>)
                || type == typeof(float[])
                || type == typeof(ReadOnlyMemory<Half>)
                || type == typeof(Embedding<Half>)
                || type == typeof(Half[]);
        }

        protected override Type? ResolveEmbeddingType(
            VectorPropertyModel vectorProperty,
            IEmbeddingGenerator embeddingGenerator,
            Type? userRequestedEmbeddingType)
            => vectorProperty.ResolveEmbeddingType<Embedding<float>>(embeddingGenerator, userRequestedEmbeddingType)
                ?? vectorProperty.ResolveEmbeddingType<Embedding<Half>>(embeddingGenerator, userRequestedEmbeddingType);
    }

    private sealed class FakeEmbeddingGenerator<TInput, TEmbedding> : IEmbeddingGenerator<TInput, TEmbedding>
        where TEmbedding : Embedding
    {
        public Task<GeneratedEmbeddings<TEmbedding>> GenerateAsync(
            IEnumerable<TInput> values,
            EmbeddingGenerationOptions? options = null,
            CancellationToken cancellationToken = default)
            => throw new UnreachableException();

        public object? GetService(Type serviceType, object? serviceKey = null)
            => throw new UnreachableException();

        public void Dispose() { }
    }
}
