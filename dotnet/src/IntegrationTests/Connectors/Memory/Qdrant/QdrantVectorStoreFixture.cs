// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Grpc.Core;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client;
using Qdrant.Client.Grpc;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

public class QdrantVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The docker client we are using to create a qdrant container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the qdrant container that we are testing with.</summary>
    private string? _containerId = null;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreFixture"/> class.
    /// </summary>
    public QdrantVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();
        this.HotelVectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(ulong)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { IsFilterable = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, DistanceFunction = DistanceFunction.ManhattanDistance }
            }
        };
        this.HotelWithGuidIdVectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(Guid)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, DistanceFunction = DistanceFunction.ManhattanDistance }
            }
        };
    }

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

    /// <summary>Gets the qdrant client connection to use for tests.</summary>
    public QdrantClient QdrantClient { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our test model.</summary>
    public VectorStoreRecordDefinition HotelVectorStoreRecordDefinition { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our test model.</summary>
    public VectorStoreRecordDefinition HotelWithGuidIdVectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Create / Recreate qdrant docker container and run it.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        this._containerId = await SetupQdrantContainerAsync(this._client);

        // Connect to qdrant.
        this.QdrantClient = new QdrantClient("localhost");

        // Create schemas for the vector store.
        var vectorParamsMap = new VectorParamsMap();
        vectorParamsMap.Map.Add("DescriptionEmbedding", new VectorParams { Size = 4, Distance = Distance.Cosine });

        // Wait for the qdrant container to be ready.
        var retryCount = 0;
        while (retryCount++ < 5)
        {
            try
            {
                await this.QdrantClient.ListCollectionsAsync();
            }
            catch (RpcException e)
            {
                if (e.StatusCode != Grpc.Core.StatusCode.Unavailable)
                {
                    throw;
                }

                await Task.Delay(1000);
            }
        }

        await this.QdrantClient.CreateCollectionAsync(
            "namedVectorsHotels",
            vectorParamsMap);

        await this.QdrantClient.CreateCollectionAsync(
            "singleVectorHotels",
            new VectorParams { Size = 4, Distance = Distance.Cosine });

        await this.QdrantClient.CreateCollectionAsync(
            "singleVectorGuidIdHotels",
            new VectorParams { Size = 4, Distance = Distance.Cosine });

        // Create test data common to both named and unnamed vectors.
        var tags = new ListValue();
        tags.Values.Add("t1");
        tags.Values.Add("t2");
        var tagsValue = new Value();
        tagsValue.ListValue = tags;

        // Create some test data using named vectors.
        var embedding = new[] { 30f, 31f, 32f, 33f };

        var namedVectors1 = new NamedVectors();
        var namedVectors2 = new NamedVectors();
        var namedVectors3 = new NamedVectors();

        namedVectors1.Vectors.Add("DescriptionEmbedding", embedding);
        namedVectors2.Vectors.Add("DescriptionEmbedding", embedding);
        namedVectors3.Vectors.Add("DescriptionEmbedding", embedding);

        List<PointStruct> namedVectorPoints =
        [
            new PointStruct
            {
                Id = 11,
                Vectors = new Vectors { Vectors_ = namedVectors1 },
                Payload = { ["HotelName"] = "My Hotel 11", ["HotelCode"] = 11, ["parking_is_included"] = true, ["Tags"] = tagsValue, ["HotelRating"] = 4.5f, ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = 12,
                Vectors = new Vectors { Vectors_ = namedVectors2 },
                Payload = { ["HotelName"] = "My Hotel 12", ["HotelCode"] = 12, ["parking_is_included"] = false, ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = 13,
                Vectors = new Vectors { Vectors_ = namedVectors3 },
                Payload = { ["HotelName"] = "My Hotel 13", ["HotelCode"] = 13, ["parking_is_included"] = false, ["Description"] = "This is a great hotel." }
            },
        ];

        await this.QdrantClient.UpsertAsync("namedVectorsHotels", namedVectorPoints);

        // Create some test data using a single unnamed vector.
        List<PointStruct> unnamedVectorPoints =
        [
            new PointStruct
            {
                Id = 11,
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 11", ["HotelCode"] = 11, ["parking_is_included"] = true, ["Tags"] = tagsValue, ["HotelRating"] = 4.5f, ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = 12,
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 12", ["HotelCode"] = 12, ["parking_is_included"] = false, ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = 13,
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 13", ["HotelCode"] = 13, ["parking_is_included"] = false, ["Description"] = "This is a great hotel." }
            },
        ];

        await this.QdrantClient.UpsertAsync("singleVectorHotels", unnamedVectorPoints);

        // Create some test data using a single unnamed vector and a guid id.
        List<PointStruct> unnamedVectorGuidIdPoints =
        [
            new PointStruct
            {
                Id = Guid.Parse("11111111-1111-1111-1111-111111111111"),
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 11", ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = Guid.Parse("22222222-2222-2222-2222-222222222222"),
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 12", ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = Guid.Parse("33333333-3333-3333-3333-333333333333"),
                Vectors = embedding,
                Payload = { ["HotelName"] = "My Hotel 13", ["Description"] = "This is a great hotel." }
            },
        ];

        await this.QdrantClient.UpsertAsync("singleVectorGuidIdHotels", unnamedVectorGuidIdPoints);
    }

    /// <summary>
    /// Delete the docker container after the test run.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task DisposeAsync()
    {
        if (this._containerId != null)
        {
            await this._client.Containers.StopContainerAsync(this._containerId, new ContainerStopParameters());
            await this._client.Containers.RemoveContainerAsync(this._containerId, new ContainerRemoveParameters());
        }
    }

    /// <summary>
    /// Setup the qdrant container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    private static async Task<string> SetupQdrantContainerAsync(DockerClient client)
    {
        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = "qdrant/qdrant",
                Tag = "latest",
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = "qdrant/qdrant",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    {"6333", new List<PortBinding> {new() {HostPort = "6333" } }},
                    {"6334", new List<PortBinding> {new() {HostPort = "6334" } }}
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "6333", default },
                { "6334", default }
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    /// <summary>
    /// A test model for the qdrant vector store.
    /// </summary>
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
    public record HotelInfo()
    {
        /// <summary>The key of the record.</summary>
        [VectorStoreRecordKey]
        public ulong HotelId { get; init; }

        /// <summary>A string metadata field.</summary>
        [VectorStoreRecordData(IsFilterable = true, IsFullTextSearchable = true)]
        public string? HotelName { get; set; }

        /// <summary>An int metadata field.</summary>
        [VectorStoreRecordData(IsFilterable = true)]
        public int HotelCode { get; set; }

        /// <summary>A  float metadata field.</summary>
        [VectorStoreRecordData(IsFilterable = true)]
        public float? HotelRating { get; set; }

        /// <summary>A bool metadata field.</summary>
        [VectorStoreRecordData(IsFilterable = true, StoragePropertyName = "parking_is_included")]
        public bool ParkingIncluded { get; set; }

        [VectorStoreRecordData]
        public List<string> Tags { get; set; } = new List<string>();

        /// <summary>A data field.</summary>
        [VectorStoreRecordData]
        public string Description { get; set; }

        /// <summary>A vector field.</summary>
        [VectorStoreRecordVector(4, IndexKind.Hnsw, DistanceFunction.ManhattanDistance)]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
    }

    /// <summary>
    /// A test model for the qdrant vector store.
    /// </summary>
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
    public record HotelInfoWithGuidId()
    {
        /// <summary>The key of the record.</summary>
        [VectorStoreRecordKey]
        public Guid HotelId { get; init; }

        /// <summary>A string metadata field.</summary>
        [VectorStoreRecordData(IsFilterable = true, IsFullTextSearchable = true)]
        public string? HotelName { get; set; }

        /// <summary>A data field.</summary>
        [VectorStoreRecordData]
        public string Description { get; set; }

        /// <summary>A vector field.</summary>
        [VectorStoreRecordVector(4, IndexKind.Hnsw, DistanceFunction.ManhattanDistance)]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
