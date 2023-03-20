// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

public interface IQdrantResult
{
    internal QdrantResponse? ResponseInfo { get; set; }
}

internal class CollectionInfoResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { get => this.ResponseInfo; 
      set => this.ResponseInfo = value; }
      
    [JsonPropertyName("result")]
    internal QdrantCollectionInfo? Result 
    { get => this.Result;
      set => this.Result = value; }

    internal class QdrantCollectionInfo
    {
        internal CollectionInfo? InfoResult { get; set; }

        [JsonPropertyName("config")]
        internal CollectionConfig? ConfigResult { get; set; }

        [JsonPropertyName("payload_schema")]
        internal PayloadInfo? PayloadProperty { get; set; }
    }

}

internal class CollectionExistsResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal bool DoesExist { get; set; }
}

internal class ListInfoResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal QdrantListInfo? Result 
    { 
        get => this.Result;
        set => this.Result = value; 
    }
      
    internal class QdrantListInfo
    {
        [JsonPropertyName("collections")]
        internal List<string>? CollectionNames { get; set; }
    }
}

internal class CreateCollectionResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal bool IsCreated { get; set; }
}

internal class DeleteCollectionResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal bool IsDeleted { get; set; }
}