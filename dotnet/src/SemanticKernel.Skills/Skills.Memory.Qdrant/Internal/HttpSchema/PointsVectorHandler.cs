using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class PointsVectorHandler : IValidatable
{
    public enum PointVectorHandlerType
    {
        Upsert,
        GetCollectionPoints,
        GetVectorPoint,
        Delete,
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }

internal async Task<IQdrantResult> ExecuteRequest(PointVectorHandlerType requestType, string collectionName, string? pointId = null)
    {
        IQdrantResult? qdrantResult = null;

        qdrantResult = requestType switch
        {
            
            PointVectorHandlerType.GetVectorPoint =>
                await this.GetVectorPointAsync(collectionName, pointId!),
            PointVectorHandlerType.Upsert =>
                await this.UpsertPointsToCollectionAsync(collectionName),
            PointVectorHandlerType.GetCollectionPoints =>
                await this.GetPointsForCollectionAsync(),
            PointVectorHandlerType.Delete =>
                await this.DeletePointFromCollectionAsync(collectionName!),
            _ => throw new ArgumentOutOfRangeException(nameof(requestType), requestType, "The request type is not invalid")
                
        };

        return qdrantResult!;
    }

    internal async Task<IQdrantResult> GetVectorPointAsync(string collectionName, string pointId )
    {
        IQdrantResult? getVectorPointResult = null;
        return getVectorPointResult!;

    }

    internal async Task<IQdrantResult> UpsertPointsToCollectionAsync(string collectionName, string pointId )
    {
        IQdrantResult? upsertPointsToCollectionResult = null;
        return upsertPointsToCollectionResult!;

    }

    internal async Task<IQdrantResult> DeletePointFromCollectionAsync(string collectionName, string pointId )
    {
        
        IQdrantResult? deletePointFromCollectionResult = null;
        return deletePointFromCollectionResult!;

    }



    #region private ================================================================================
    private string? _collectionName;
    private HttpClient? _client;
    private string _vectorPointId;
    #endregion

}
