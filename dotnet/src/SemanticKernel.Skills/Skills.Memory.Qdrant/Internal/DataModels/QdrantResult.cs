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
    public QdrantCollectionInfo? Result 
    { get => this.Result;
      set => this.Result = value; }

    public class QdrantCollectionInfo
    {
        public CollectionInfo? InfoResult { get; set; }

        [JsonPropertyName("config")]
        public CollectionConfig? ConfigResult { get; set; }

        [JsonPropertyName("payload_schema")]
        public PayloadInfo? PayloadProperty { get; set; }
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

internal class RetrievePointResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal Points? VectorPoint { get; set; }
    
}

internal class RetrieveAllPointsResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal QdrantPointsInfo? Result { get; set; }

    internal class QdrantPointsInfo
    {
        [JsonPropertyName("points")]
        internal Points[]? PointCollection { get; set; }

        [JsonPropertyName("next_page_offset")]
        internal int? NextPageOffset { get; set; }
    }
}

internal class UpsertPointResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal QdrantUpsertInfo? Result { get; set; }

    internal class QdrantUpsertInfo
    {
        [JsonPropertyName("operation_id")]
        internal int? OperationId { get; set; }

        [JsonPropertyName("status")]
        internal string? UpdateStatus { get; set; }
    }

}

internal class DeletePointResult : IQdrantResult
{
    public QdrantResponse? ResponseInfo 
    { 
        get => this.ResponseInfo; 
        set => this.ResponseInfo = value; 
    }

    [JsonPropertyName("result")]
    internal QdrantDeleteInfo? Result { get; set; }

    internal class QdrantDeleteInfo
    {
        [JsonPropertyName("operation_id")]
        internal int? OperationId { get; set; }

        [JsonPropertyName("status")]
        internal string? DeleteStatus { get; set; }
    }

}