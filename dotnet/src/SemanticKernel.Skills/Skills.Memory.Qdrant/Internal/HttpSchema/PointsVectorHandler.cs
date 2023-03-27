using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

public class PointsVectorHandler : IValidatable
{
    public enum PointVectorHandlerType
    {
        Upsert,
        GetCollectionPoints,
        GetVectorPoint,
        Delete,
    }

    public static PointsVectorHandler Init(HttpClient httpClient, string collectionName)
    {
        return new PointsVectorHandler(httpClient, collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }

    internal async Task<IQdrantResult> ExecuteRequest(PointVectorHandlerType requestType, string collectionName, int? pointId = null, string? pointjsondata = null)
    {
        IQdrantResult? qdrantResult = null;

        qdrantResult = requestType switch
        {
            
            PointVectorHandlerType.GetVectorPoint =>
                await this.RetrieveVectorPointAsync(collectionName, pointId),
            PointVectorHandlerType.Upsert =>
                await this.UpsertPointToCollectionAsync(collectionName, pointjsondata!),
            PointVectorHandlerType.GetCollectionPoints =>
                await this.GetPointsForCollectionAsync(collectionName),
            PointVectorHandlerType.Delete =>
                await this.DeletePointFromCollectionAsync(collectionName!, pointId),
            _ => throw new ArgumentOutOfRangeException(nameof(requestType), requestType, "The request type is not invalid")
                
        };

        return qdrantResult!;
    }

    internal async Task<IQdrantResult> RetrieveVectorPointAsync(string collectionName, int? pointId )
    {
        IQdrantResult? retrieveVectorPointResult = null;
        
        string qdrantRetrievePointUrl = QdrantApiUrlConstants.RetrievePointUrl(collectionName, pointId.ToString()!);

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");
        Verify.NotNull(pointId, "The point id must be defined");

        try 
        {
            retrieveVectorPointResult = await HttpRequest.SendHttpFromJsonAsync<RetrievePointResult, IQdrantResult>(
                        this._client!,
                        HttpMethod.Get,
                        qdrantRetrievePointUrl,
                        null, null);
        }
        catch
        {
            retrieveVectorPointResult = new RetrievePointResult();
            retrieveVectorPointResult.ResponseInfo = null;
        }

        return retrieveVectorPointResult!;

    }

    internal async Task<IQdrantResult> UpsertPointToCollectionAsync(string collectionName, string vectorData)
    {
        IQdrantResult? upsertPointsToCollectionResult = null;

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");
        Verify.NotNullOrEmpty(vectorData, "The vector/point data must be defined");

        Points? pointData = JsonSerializer.Deserialize<Points>(vectorData);
        PointUpsertParams? pointParams = new PointUpsertParams
        {
            PointData = new List<Points>{pointData!}
        };

        string qdrantUpsertPointUrl = QdrantApiUrlConstants.UpsertPointsUrl(collectionName);
       
        try
        {
            upsertPointsToCollectionResult = await HttpRequest.SendHttpFromJsonAsync<UpsertPointResult, PointUpsertParams>(
                        this._client!,
                        HttpMethod.Put,
                        qdrantUpsertPointUrl,
                        pointParams, null);
        }
        catch
        {
            upsertPointsToCollectionResult = new UpsertPointResult();
            upsertPointsToCollectionResult.ResponseInfo = null;
        }
        
        return upsertPointsToCollectionResult!;

    }

    internal async Task<IQdrantResult> GetPointsForCollectionAsync(string collectionName)
    {
        IQdrantResult? getPointsforCollectionResult = null;
        PointParams? pointParams = new PointParams
        {
            WithPayload = true,
            WithVector = true,
            Limit=0,
            Offset=0,
        };

        string qdrantGetAllPointsUrl = QdrantApiUrlConstants.GetPointsForCollectionUrl(collectionName);

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");

        try 
        {
            getPointsforCollectionResult = await HttpRequest.SendHttpFromJsonAsync<RetrieveAllPointsResult, PointParams>(
                        this._client!,
                        HttpMethod.Post,
                        qdrantGetAllPointsUrl,
                        pointParams, null);
        }
        catch
        {
            getPointsforCollectionResult = new RetrieveAllPointsResult();
            getPointsforCollectionResult.ResponseInfo = null;
        }

        return getPointsforCollectionResult!;

    }

    internal async Task<IQdrantResult> DeletePointFromCollectionAsync(string collectionName, int? pointId )
    {
        
        IQdrantResult? deletePointFromCollectionResult = null;

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");
        Verify.NotNull(pointId, "The point id must be defined");
        PointDeleteParams deleteParams = new PointDeleteParams()
        {
            PointIds = new int[] { pointId!.Value }
        };

        string qdrantDeletePointUrl = QdrantApiUrlConstants.DeletePointUrl(collectionName);

        try 
        {
            deletePointFromCollectionResult = await HttpRequest.SendHttpFromJsonAsync<DeletePointResult, PointDeleteParams>(
                        this._client!,
                        HttpMethod.Post,
                        qdrantDeletePointUrl,
                        deleteParams, null);
        }
        catch
        {
            deletePointFromCollectionResult = new DeletePointResult();
            deletePointFromCollectionResult.ResponseInfo = null;
        }


        return deletePointFromCollectionResult!;

    }


    #region private ================================================================================
    private string? _collectionName;
    private HttpClient? _client;
    private string? _vectorPointId;

    private PointsVectorHandler(HttpClient client, string collectionName)
    {
        this._client = client;
        this._collectionName = collectionName;
    }

    #endregion

}
