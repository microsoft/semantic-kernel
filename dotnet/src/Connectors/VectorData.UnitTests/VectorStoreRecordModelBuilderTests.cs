// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;
using Xunit;

namespace VectorData.UnitTests;

#pragma warning disable CA2000 // Dispose objects before losing scope

public class VectorStoreRecordModelBuilderTests
{
    [Fact]
    public void Default_embedding_generator_without_record_definition()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();
        var model = new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), vectorStoreRecordDefinition: null, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(ReadOnlyMemory<float>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_clr_type_and_record_definition()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<Half>>();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    // The following configures the property to be ReadOnlyMemory<Half> (non-default embedding type for this connector)
                    EmbeddingType = typeof(ReadOnlyMemory<Half>)
                }
            ]
        };

        var model = new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), recordDefinition, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(ReadOnlyMemory<Half>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_dynamic()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
            ]
        };

        var model = new CustomModelBuilder().Build(typeof(Dictionary<string, object?>), recordDefinition, embeddingGenerator);

        // The embedding's .NET type (Embedding<float>) is inferred from the embedding generator.
        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(ReadOnlyMemory<float>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Default_embedding_generator_with_dynamic_and_non_default_EmbeddingType()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<Half>>();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingType = typeof(ReadOnlyMemory<Half>)
                }
            ]
        };

        var model = new CustomModelBuilder().Build(typeof(Dictionary<string, object?>), recordDefinition, embeddingGenerator);

        Assert.Same(embeddingGenerator, model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(string), model.VectorProperty.Type);
        Assert.Same(typeof(ReadOnlyMemory<Half>), model.VectorProperty.EmbeddingType);
    }

    [Fact]
    public void Property_embedding_generator_takes_precedence_over_default_generator()
    {
        using var propertyEmbeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();
        using var defaultEmbeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(string), dimensions: 3)
                {
                    EmbeddingGenerator = propertyEmbeddingGenerator
                }
            ]
        };

        var model = new CustomModelBuilder().Build(typeof(Dictionary<string, object?>), recordDefinition, defaultEmbeddingGenerator);

        Assert.Same(propertyEmbeddingGenerator, model.VectorProperty.EmbeddingGenerator);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Embedding_property_type_with_default_embedding_generator_ignores_generator(bool dynamic)
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<float>>();

        var model = dynamic
            ? new CustomModelBuilder().Build(
                typeof(Dictionary<string, object?>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                        new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                        new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(ReadOnlyMemory<float>), dimensions: 3)
                    ]
                },
                embeddingGenerator)
            : new CustomModelBuilder().Build(typeof(RecordWithEmbeddingVectorProperty), vectorStoreRecordDefinition: null, embeddingGenerator);

        Assert.Null(model.VectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(ReadOnlyMemory<float>), model.VectorProperty.Type);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Custom_input_type(bool dynamic)
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<Customer, Embedding<float>>();

        // TODO: Allow custom input type without a record definition (i.e. generic attribute)
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty<Customer>(nameof(RecordWithEmbeddingVectorProperty.Embedding), dimensions: 3)
            ]
        };

        var model = dynamic
            ? new CustomModelBuilder().Build(typeof(Dictionary<string, object?>), recordDefinition, embeddingGenerator)
            : new CustomModelBuilder().Build(typeof(RecordWithCustomerVectorProperty), recordDefinition, embeddingGenerator);

        var vectorProperty = model.VectorProperty;

        Assert.Same(embeddingGenerator, vectorProperty.EmbeddingGenerator);
        Assert.Same(typeof(Customer), vectorProperty.Type);
        Assert.Same(typeof(ReadOnlyMemory<float>), vectorProperty.EmbeddingType);
    }

    [Fact]
    public void Incompatible_embedding_on_embedding_generator_throws()
    {
        // Embedding<long> is not a supported embedding type by the connector
        using var embeddingGenerator = new FakeEmbeddingGenerator<string, Embedding<long>>();

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), vectorStoreRecordDefinition: null, embeddingGenerator));

        Assert.Equal($"Embedding generator '{typeof(FakeEmbeddingGenerator<,>).Name}' is incompatible with the required input and output types. The property input type must be 'String, DataContent', and the output type must be 'ReadOnlyMemory<float>, ReadOnlyMemory<Half>'.", exception.Message);
    }

    [Fact]
    public void Incompatible_input_on_embedding_generator_throws()
    {
        // int is not a supported input type for the embedding generator
        using var embeddingGenerator = new FakeEmbeddingGenerator<int, Embedding<float>>();

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), vectorStoreRecordDefinition: null, embeddingGenerator));

        Assert.Equal($"Embedding generator '{typeof(FakeEmbeddingGenerator<,>).Name}' is incompatible with the required input and output types. The property input type must be 'String, DataContent', and the output type must be 'ReadOnlyMemory<float>, ReadOnlyMemory<Half>'.", exception.Message);
    }

    [Fact]
    public void Non_embedding_vector_property_without_embedding_generator_throws()
    {
        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithStringVectorProperty), vectorStoreRecordDefinition: null, defaultEmbeddingGenerator: null));

        Assert.Equal($"Property '{nameof(RecordWithStringVectorProperty.Embedding)}' has non-Embedding type 'String', but no embedding generator is configured.", exception.Message);
    }

    [Fact]
    public void Embedding_property_type_with_property_embedding_generator_throws()
    {
        using var embeddingGenerator = new FakeEmbeddingGenerator<int, Embedding<float>>();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(RecordWithEmbeddingVectorProperty.Id), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(RecordWithEmbeddingVectorProperty.Name), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(RecordWithEmbeddingVectorProperty.Embedding), typeof(ReadOnlyMemory<float>), dimensions: 3)
                {
                    EmbeddingGenerator = embeddingGenerator
                }
            ]
        };

        var exception = Assert.Throws<InvalidOperationException>(() =>
            new CustomModelBuilder().Build(typeof(RecordWithEmbeddingVectorProperty), recordDefinition, embeddingGenerator));

        Assert.Equal(
            $"Property '{nameof(RecordWithEmbeddingVectorProperty.Embedding)}' has embedding type 'ReadOnlyMemory`1', but an embedding generator is configured on the property. Remove the embedding generator or change the property's .NET type to a non-embedding input type to the generator (e.g. string).",
            exception.Message);
    }

    public class RecordWithStringVectorProperty
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordData]
        public string Name { get; set; }

        [VectorStoreRecordVector(Dimensions: 3)]
        public string Embedding { get; set; }
    }

    public class RecordWithEmbeddingVectorProperty
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordData]
        public string Name { get; set; }

        [VectorStoreRecordVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    public class RecordWithCustomerVectorProperty
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordData]
        public string Name { get; set; }

        [VectorStoreRecordVector(Dimensions: 3)]
        public Customer Embedding { get; set; }
    }

    public class Customer
    {
        public string FirstName { get; set; }
        public string LastName { get; set; }
    }

    private sealed class CustomModelBuilder(VectorStoreRecordModelBuildingOptions? options = null)
        : VectorStoreRecordModelBuilder(options ?? s_defaultOptions)
    {
        private static readonly VectorStoreRecordModelBuildingOptions s_defaultOptions = new()
        {
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true,
            RequiresAtLeastOneVector = false,

            SupportedKeyPropertyTypes = [typeof(string), typeof(int)],
            SupportedDataPropertyTypes = [typeof(string), typeof(int)],
            SupportedEnumerableDataPropertyElementTypes = [typeof(string), typeof(int)],
            SupportedVectorPropertyTypes = [typeof(ReadOnlyMemory<float>), typeof(ReadOnlyMemory<Half>)]
        };

        protected override void SetupEmbeddingGeneration(
            VectorStoreRecordVectorPropertyModel vectorProperty,
            IEmbeddingGenerator embeddingGenerator,
            Type? embeddingType)
        {
            if (!vectorProperty.TrySetupEmbeddingGeneration<Embedding<float>, ReadOnlyMemory<float>>(embeddingGenerator, embeddingType)
                && !vectorProperty.TrySetupEmbeddingGeneration<Embedding<Half>, ReadOnlyMemory<Half>>(embeddingGenerator, embeddingType))
            {
                throw new InvalidOperationException(
                    string.Format(
                        VectorDataStrings.IncompatibleEmbeddingGenerator,
                        embeddingGenerator.GetType().Name,
                        string.Join(", ", vectorProperty.GetSupportedInputTypes().Select(t => t.Name)),
                        "ReadOnlyMemory<float>, ReadOnlyMemory<Half>"));
            }
        }
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
