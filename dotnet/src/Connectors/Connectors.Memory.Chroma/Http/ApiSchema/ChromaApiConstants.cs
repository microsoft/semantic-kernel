// Copyright (c) Microsoft. All rights reserved.

using System;


/// <summary>
/// A Constant class of the url constant strings for each of the Chroma API commands. This class is used to
/// correct assign the right API calls to connect, create, delete, and get embeddings data from a Chroma VectorDB instance.
/// </summary>

public static class ChromaApiConstants
{
    /// <summary>
    /// The collection name to be used with API calls for collection and associated vectors
    /// </summary>
    public static string collection_name { get; set; }

    /// <summary>
    /// The root of the Chroma API path for all API calls 
    /// </summary>
    public static readonly string APIRootPath = "/api/v1";

    /// <summary>
    /// The GET API call for Chroma version.
    /// </summary>
    public static readonly string GetVersion = "/api/v1/version";

    /// <summary>
    /// The GET API call for Chroma heartbeat/test.
    /// </summary>
    public static readonly string GetHeartbeat = "/api/v1/heartbeat";

    /// <summary>
    /// The GET API call for listing all collections stored with Chroma.
    /// </summary>
    public static readonly string CollectionsGetList = "/api/v1/collections";

    /// <summary>
    /// The GET API call for gettting one collection by name stored with Chroma.
    /// </summary>
    public static readonly string CollectionsGetCollection = $"/api/v1/collections/{collection_name}";

    /// <summary>
    /// The POST API call for creating a collection to store in Chroma.
    /// </summary>
    public static readonly string CollectionPostCreate = "/api/v1/collections/";

    /// <summary>
    /// The DELETE API call for removing a collection stored with Chroma.
    /// </summary>
    public static readonly string CollectionDelete = $"/api/v1/collections/{collection_name}/delete";

    /// <summary>
    /// The GET API call for gettting vector count for one collection by name stored with Chroma.
    /// </summary>
    public static readonly string CollectionVectorCount = $"/api/v1/collections/{collection_name}/count";

    /// <summary>
    /// The POST API call for adding vector for one collection by name stored with Chroma.
    /// </summary>
    public static readonly string CollectionPostVectorAdd = $"/api/v1/collections/{collection_name}/add"



}
