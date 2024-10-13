// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Microsoft.Extensions.VectorData;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
/// <summary>
/// Does setup and teardown of redis docker container and associated test data.
/// </summary>
public class RedisVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The docker client we are using to create a redis container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the redis container that we are testing with.</summary>
    private string? _containerId = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorStoreFixture"/> class.
    /// </summary>
    public RedisVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();
        this.VectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)) { IsFullTextSearchable = true },
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4 },
                new VectorStoreRecordDataProperty("Tags", typeof(string[])) { IsFilterable = true },
                new VectorStoreRecordDataProperty("FTSTags", typeof(string[])) { IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("LastRenovationDate", typeof(DateTimeOffset)),
                new VectorStoreRecordDataProperty("Rating", typeof(double)),
                new VectorStoreRecordDataProperty("Address", typeof(HotelAddress))
            }
        };
        this.BasicVectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)) { IsFullTextSearchable = true },
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4 },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("Rating", typeof(double)),
            }
        };
    }

    /// <summary>Gets the redis database connection to use for tests.</summary>
    public IDatabase Database { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our test model.</summary>
    public VectorStoreRecordDefinition VectorStoreRecordDefinition { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our basic test model.</summary>
    public VectorStoreRecordDefinition BasicVectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Create / Recreate redis docker container, create an index and add test data.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        this._containerId = await SetupRedisContainerAsync(this._client);

        // Connect to redis.
        ConnectionMultiplexer redis = ConnectionMultiplexer.Connect("localhost:6379,connectTimeout=60000,connectRetry=5");
        this.Database = redis.GetDatabase();

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
=======
>>>>>>> upstream/main
        // Create a JSON index.
        var jsonSchema = new Schema();
        jsonSchema.AddTagField(new FieldName("$.HotelName", "HotelName"));
        jsonSchema.AddNumericField(new FieldName("$.HotelCode", "HotelCode"));
        jsonSchema.AddTextField(new FieldName("$.Description", "Description"));
        jsonSchema.AddTagField(new FieldName("$.Tags", "Tags"));
        jsonSchema.AddTextField(new FieldName("$.FTSTags", "FTSTags"));
        jsonSchema.AddVectorField(new FieldName("$.DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
<<<<<<< main
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        // Create a schema for the vector store.
        var schema = new Schema();
        schema.AddTextField(new FieldName("$.HotelName", "HotelName"));
        schema.AddNumericField(new FieldName("$.HotelCode", "HotelCode"));
        schema.AddTextField(new FieldName("$.Description", "Description"));
        schema.AddVectorField(new FieldName("$.DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });
        var jsonCreateParams = new FTCreateParams().AddPrefix("jsonhotels:").On(IndexDataType.JSON);
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await this.Database.FT().CreateAsync("jsonhotels", jsonCreateParams, jsonSchema);

        // Create a hashset index.
        var hashSchema = new Schema();
        hashSchema.AddTagField(new FieldName("HotelName", "HotelName"));
        hashSchema.AddNumericField(new FieldName("HotelCode", "HotelCode"));
        hashSchema.AddTextField(new FieldName("Description", "Description"));
        hashSchema.AddVectorField(new FieldName("DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });

        var hashsetCreateParams = new FTCreateParams().AddPrefix("hashhotels:").On(IndexDataType.HASH);
        await this.Database.FT().CreateAsync("hashhotels", hashsetCreateParams, hashSchema);
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        await this.Database.FT().CreateAsync("jsonhotels", jsonCreateParams, schema);
=======
        await this.Database.FT().CreateAsync("jsonhotels", jsonCreateParams, jsonSchema);
>>>>>>> upstream/main

        // Create a hashset index.
        var hashSchema = new Schema();
        hashSchema.AddTagField(new FieldName("HotelName", "HotelName"));
        hashSchema.AddNumericField(new FieldName("HotelCode", "HotelCode"));
        hashSchema.AddTextField(new FieldName("Description", "Description"));
        hashSchema.AddVectorField(new FieldName("DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });

        var hashsetCreateParams = new FTCreateParams().AddPrefix("hashhotels:").On(IndexDataType.HASH);
<<<<<<< main
        await this.Database.FT().CreateAsync("hashhotels", hashsetCreateParams, schema);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await this.Database.FT().CreateAsync("hashhotels", hashsetCreateParams, hashSchema);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        // Create some test data.
        var address = new HotelAddress { City = "Seattle", Country = "USA" };
        var embedding = new[] { 30f, 31f, 32f, 33f };

        // Add JSON test data.
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-1", "$", new
        {
            HotelName = "My Hotel 1",
            HotelCode = 1,
            Description = "This is a great hotel.",
            DescriptionEmbedding = embedding,
            Tags = new[] { "pool", "air conditioning", "concierge" },
            FTSTags = new[] { "pool", "air conditioning", "concierge" },
            parking_is_included = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = address
        });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-2", "$", new { HotelName = "My Hotel 2", HotelCode = 2, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-3", "$", new { HotelName = "My Hotel 3", HotelCode = 3, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-4-Invalid", "$", new { HotelId = "AnotherId", HotelName = "My Invalid Hotel", HotelCode = 4, Description = "This is an invalid hotel.", DescriptionEmbedding = embedding, parking_is_included = false });

        // Add hashset test data.
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        await this.Database.HashSetAsync("hashhotels:BaseSet-1", new HashEntry[]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:BaseSet-1", new HashEntry[]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-1", new HashEntry[]
=======
>>>>>>> Stashed changes
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-1", new HashEntry[]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:HBaseSet-1", new HashEntry[]
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-1", new HashEntry[]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await this.Database.HashSetAsync("hashhotels:HBaseSet-1", new HashEntry[]
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            new("HotelName", "My Hotel 1"),
            new("HotelCode", 1),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", true),
            new("Rating", 3.6)
        });
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        await this.Database.HashSetAsync("hashhotels:BaseSet-2", new HashEntry[]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:BaseSet-2", new HashEntry[]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-2", new HashEntry[]
=======
>>>>>>> Stashed changes
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-2", new HashEntry[]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:HBaseSet-2", new HashEntry[]
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-2", new HashEntry[]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await this.Database.HashSetAsync("hashhotels:HBaseSet-2", new HashEntry[]
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            new("HotelName", "My Hotel 2"),
            new("HotelCode", 2),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        await this.Database.HashSetAsync("hashhotels:BaseSet-3", new HashEntry[]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:BaseSet-3", new HashEntry[]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-3", new HashEntry[]
=======
>>>>>>> Stashed changes
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-3", new HashEntry[]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:HBaseSet-3", new HashEntry[]
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-3", new HashEntry[]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await this.Database.HashSetAsync("hashhotels:HBaseSet-3", new HashEntry[]
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            new("HotelName", "My Hotel 3"),
            new("HotelCode", 3),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        await this.Database.HashSetAsync("hashhotels:BaseSet-4-Invalid", new HashEntry[]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:BaseSet-4-Invalid", new HashEntry[]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-4-Invalid", new HashEntry[]
=======
>>>>>>> Stashed changes
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-4-Invalid", new HashEntry[]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await this.Database.HashSetAsync("hashhotels:HBaseSet-4-Invalid", new HashEntry[]
=======
        await this.Database.HashSetAsync("hashhotels:BaseSet-4-Invalid", new HashEntry[]
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await this.Database.HashSetAsync("hashhotels:HBaseSet-4-Invalid", new HashEntry[]
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        {
            new("HotelId", "AnotherId"),
            new("HotelName", "My Invalid Hotel"),
            new("HotelCode", 4),
            new("Description", "This is an invalid hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
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
    /// Setup the redis container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    private static async Task<string> SetupRedisContainerAsync(DockerClient client)
    {
        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = "redis/redis-stack",
                Tag = "latest",
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = "redis/redis-stack",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
=======
>>>>>>> Stashed changes
=======
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}},
                    {"8001", new List<PortBinding> {new() {HostPort = "8001"}}}
=======
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}},
                    {"8001", new List<PortBinding> {new() {HostPort = "8001"}}}
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                { "6379", default }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                { "6379", default }
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
                { "6379", default }
=======
>>>>>>> Stashed changes
=======
                { "6379", default }
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
                { "6379", default },
                { "8001", default }
=======
                { "6379", default }
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
                { "6379", default },
                { "8001", default }
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        await Task.Delay(1000);

=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        await Task.Delay(1000);

>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        return container.ID;
    }

    /// <summary>
    /// A test model for the vector store that has complex properties as supported by JSON redis mode.
    /// </summary>
    public class Hotel
    {
        [VectorStoreRecordKey]
        public string HotelId { get; init; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string HotelName { get; init; }

        [VectorStoreRecordData(IsFilterable = true)]
        public int HotelCode { get; init; }

        [VectorStoreRecordData(IsFullTextSearchable = true)]
        public string Description { get; init; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }

#pragma warning disable CA1819 // Properties should not return arrays
        [VectorStoreRecordData(IsFilterable = true)]
        public string[] Tags { get; init; }

        [VectorStoreRecordData(IsFullTextSearchable = true)]
        public string[] FTSTags { get; init; }
#pragma warning restore CA1819 // Properties should not return arrays

        [JsonPropertyName("parking_is_included")]
        [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
        public bool ParkingIncluded { get; init; }

        [VectorStoreRecordData]
        public DateTimeOffset LastRenovationDate { get; init; }

        [VectorStoreRecordData]
        public double Rating { get; init; }

        [VectorStoreRecordData]
        public HotelAddress Address { get; init; }
    }

    /// <summary>
    /// A test model for the vector store to simulate a complex type.
    /// </summary>
    public class HotelAddress
    {
        public string City { get; init; }
        public string Country { get; init; }
    }

    /// <summary>
    /// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
    /// </summary>
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public class BasicHotel
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public class BasicHotel
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    public class BasicHotel
=======
>>>>>>> Stashed changes
=======
    public class BasicHotel
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    public class BasicHotel<TVectorElement>
=======
    public class BasicHotel
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
    public class BasicHotel<TVectorElement>
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
    {
        [VectorStoreRecordKey]
        public string HotelId { get; init; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string HotelName { get; init; }

        [VectorStoreRecordData(IsFilterable = true)]
        public int HotelCode { get; init; }

        [VectorStoreRecordData(IsFullTextSearchable = true)]
        public string Description { get; init; }

        [VectorStoreRecordVector(4)]
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }
=======
>>>>>>> Stashed changes
=======
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        public ReadOnlyMemory<TVectorElement>? DescriptionEmbedding { get; init; }
=======
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
        public ReadOnlyMemory<TVectorElement>? DescriptionEmbedding { get; init; }
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

        [JsonPropertyName("parking_is_included")]
        [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
        public bool ParkingIncluded { get; init; }

        [VectorStoreRecordData]
        public double Rating { get; init; }
    }
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
=======
>>>>>>> upstream/main

    /// <summary>
    /// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
    /// </summary>
    public class BasicFloat32Hotel : BasicHotel<float>
    {
    }

    /// <summary>
    /// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
    /// </summary>
    public class BasicFloat64Hotel : BasicHotel<double>
    {
    }
<<<<<<< main
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
