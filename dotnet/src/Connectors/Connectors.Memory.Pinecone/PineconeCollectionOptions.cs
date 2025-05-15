// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class PineconeCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly PineconeCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeCollectionOptions"/> class.
    /// </summary>
    public PineconeCollectionOptions()
    {
    }

    internal PineconeCollectionOptions(PineconeCollectionOptions? source) : base(source)
    {
        this.IndexNamespace = source?.IndexNamespace;
        this.ServerlessIndexCloud = source?.ServerlessIndexCloud ?? Default.ServerlessIndexCloud;
        this.ServerlessIndexRegion = source?.ServerlessIndexRegion ?? Default.ServerlessIndexRegion;
    }

    /// <summary>
    /// Gets or sets the value for a namespace within the Pinecone index that will be used for operations involving records (Get, Upsert, Delete)."/>
    /// </summary>
    public string? IndexNamespace { get; set; }

    /// <summary>
    /// Gets or sets the value for public cloud where the serverless index is hosted.
    /// </summary>
    /// <remarks>
    /// This value is only used when creating a new Pinecone index. Default value is 'aws'.
    /// </remarks>
    public string ServerlessIndexCloud { get; set; } = "aws";

    /// <summary>
    /// Gets or sets the value for region where the serverless index is created.
    /// </summary>
    /// <remarks>
    /// This option is only used when creating a new Pinecone index. Default value is 'us-east-1'.
    /// </remarks>
    public string ServerlessIndexRegion { get; set; } = "us-east-1";
}
