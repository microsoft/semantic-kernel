// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Azure.Identity;
using Docker.DotNet;
using Docker.DotNet.Models;
using Grpc.Core;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using Qdrant.Client.Grpc;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

public class QdrantVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The docker client we are using to create a qdrant container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the qdrant container that we are testing with.</summary>
    private string? _containerId = null;

    /// <summary>The vector dimension.</summary>
    private const int VectorDimensions = 1536;

    /// <summary>
    /// Test Configuration setup.
    /// </summary>
    private static readonly IConfigurationRoot s_configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<QdrantVectorStoreFixture>()
        .Build();

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
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { IsIndexed = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("LastRenovationDate", typeof(DateTimeOffset)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), VectorDimensions) { DistanceFunction = DistanceFunction.ManhattanDistance }
            }
        };
        this.HotelWithGuidIdVectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(Guid)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), VectorDimensions) { DistanceFunction = DistanceFunction.ManhattanDistance }
            }
        };
        AzureOpenAIConfiguration? embeddingsConfig = s_configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(embeddingsConfig);
        Assert.NotEmpty(embeddingsConfig.DeploymentName);
        Assert.NotEmpty(embeddingsConfig.Endpoint);
        this.EmbeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
            deploymentName: embeddingsConfig.DeploymentName,
            endpoint: embeddingsConfig.Endpoint,
            credential: new AzureCliCredential());
    }

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

    /// <summary>Gets the qdrant client connection to use for tests.</summary>
    public QdrantClient QdrantClient { get; private set; }

    /// <summary>
    /// Gets the embedding generator to use for generating embeddings for text.
    /// </summary>
    public ITextEmbeddingGenerationService EmbeddingGenerator { get; private set; }

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
        vectorParamsMap.Map.Add("DescriptionEmbedding", new VectorParams { Size = VectorDimensions, Distance = Distance.Cosine });

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
            new VectorParams { Size = VectorDimensions, Distance = Distance.Cosine });

        await this.QdrantClient.CreateCollectionAsync(
            "singleVectorGuidIdHotels",
            new VectorParams { Size = VectorDimensions, Distance = Distance.Cosine });

        // Create test data common to both named and unnamed vectors.
        var tags = new ListValue();
        tags.Values.Add("t11.1");
        tags.Values.Add("t11.2");
        var tagsValue = new Value();
        tagsValue.ListValue = tags;

        var tags2 = new ListValue();
        tags2.Values.Add("t13.1");
        tags2.Values.Add("t13.2");
        var tagsValue2 = new Value();
        tagsValue2.ListValue = tags2;

        // Create some test data using named vectors.
        var embedding = await this.EmbeddingGenerator.GenerateEmbeddingAsync("This is a great hotel.");
        var embeddingArray = embedding.ToArray();

        var namedVectors1 = new NamedVectors();
        var namedVectors2 = new NamedVectors();
        var namedVectors3 = new NamedVectors();
        var namedVectors4 = new NamedVectors();

        namedVectors1.Vectors.Add("DescriptionEmbedding", embeddingArray);
        namedVectors2.Vectors.Add("DescriptionEmbedding", embeddingArray);
        namedVectors3.Vectors.Add("DescriptionEmbedding", embeddingArray);
        namedVectors4.Vectors.Add("DescriptionEmbedding", embeddingArray);

        List<PointStruct> namedVectorPoints =
        [
            new PointStruct
            {
                Id = 11,
                Vectors = new Vectors { Vectors_ = namedVectors1 },
                Payload = { ["HotelName"] = "My Hotel 11", ["HotelCode"] = 11, ["parking_is_included"] = true, ["Tags"] = tagsValue, ["HotelRating"] = 4.5f, ["Description"] = "This is a great hotel.", ["LastRenovationDate"] = "2025-02-10T05:10:15.0000000Z" }
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
                Payload = { ["HotelName"] = "My Hotel 13", ["HotelCode"] = 13, ["parking_is_included"] = false, ["Tags"] = tagsValue2, ["Description"] = "This is a great hotel.", ["LastRenovationDate"] = "2020-02-01T00:00:00.0000000Z" }
            },
            new PointStruct
            {
                Id = 14,
                Vectors = new Vectors { Vectors_ = namedVectors4 },
                Payload = { ["HotelName"] = "My Hotel 14", ["HotelCode"] = 14, ["parking_is_included"] = false, ["HotelRating"] = 4.5f, ["Description"] = "This is a great hotel." }
            },
        ];

        await this.QdrantClient.UpsertAsync("namedVectorsHotels", namedVectorPoints);

        // Create some test data using a single unnamed vector.
        List<PointStruct> unnamedVectorPoints =
        [
            new PointStruct
            {
                Id = 11,
                Vectors = embeddingArray,
                Payload = { ["HotelName"] = "My Hotel 11", ["HotelCode"] = 11, ["parking_is_included"] = true, ["Tags"] = tagsValue, ["HotelRating"] = 4.5f, ["Description"] = "This is a great hotel.", ["LastRenovationDate"] = "2025-02-10T05:10:15.0000000Z" }
            },
            new PointStruct
            {
                Id = 12,
                Vectors = embeddingArray,
                Payload = { ["HotelName"] = "My Hotel 12", ["HotelCode"] = 12, ["parking_is_included"] = false, ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = 13,
                Vectors = embeddingArray,
                Payload = { ["HotelName"] = "My Hotel 13", ["HotelCode"] = 13, ["parking_is_included"] = false, ["Tags"] = tagsValue2, ["Description"] = "This is a great hotel.", ["LastRenovationDate"] = "2020-02-01T00:00:00.0000000Z" }
            },
        ];

        await this.QdrantClient.UpsertAsync("singleVectorHotels", unnamedVectorPoints);

        // Create some test data using a single unnamed vector and a guid id.
        List<PointStruct> unnamedVectorGuidIdPoints =
        [
            new PointStruct
            {
                Id = Guid.Parse("11111111-1111-1111-1111-111111111111"),
                Vectors = embeddingArray,
                Payload = { ["HotelName"] = "My Hotel 11", ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = Guid.Parse("22222222-2222-2222-2222-222222222222"),
                Vectors = embeddingArray,
                Payload = { ["HotelName"] = "My Hotel 12", ["Description"] = "This is a great hotel." }
            },
            new PointStruct
            {
                Id = Guid.Parse("33333333-3333-3333-3333-333333333333"),
                Vectors = embeddingArray,
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
        [VectorStoreRecordData(IsIndexed = true, IsFullTextIndexed = true)]
        public string? HotelName { get; set; }

        /// <summary>An int metadata field.</summary>
        [VectorStoreRecordData(IsIndexed = true)]
        public int HotelCode { get; set; }

        /// <summary>A  float metadata field.</summary>
        [VectorStoreRecordData(IsIndexed = true)]
        public float? HotelRating { get; set; }

        /// <summary>A bool metadata field.</summary>
        [VectorStoreRecordData(IsIndexed = true, StoragePropertyName = "parking_is_included")]
        public bool ParkingIncluded { get; set; }

        [VectorStoreRecordData(IsIndexed = true)]
        public List<string> Tags { get; set; } = new List<string>();

        /// <summary>A datetime metadata field.</summary>
        [VectorStoreRecordData(IsIndexed = true)]
        public DateTimeOffset? LastRenovationDate { get; set; }

        /// <summary>A data field.</summary>
        [VectorStoreRecordData]
        public string Description { get; set; }

        /// <summary>A vector field.</summary>
        [VectorStoreRecordVector(VectorDimensions, DistanceFunction = DistanceFunction.ManhattanDistance, IndexKind = IndexKind.Hnsw)]
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
        [VectorStoreRecordData(IsIndexed = true, IsFullTextIndexed = true)]
        public string? HotelName { get; set; }

        /// <summary>A data field.</summary>
        [VectorStoreRecordData]
        public string Description { get; set; }

        /// <summary>A vector field.</summary>
        [VectorStoreRecordVector(VectorDimensions, DistanceFunction = DistanceFunction.ManhattanDistance, IndexKind = IndexKind.Hnsw)]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
