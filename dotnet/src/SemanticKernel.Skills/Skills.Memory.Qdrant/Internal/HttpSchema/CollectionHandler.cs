using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class CollectionHandler : IValidatable
{
    public enum CollectionHandlerType
    {
        Create,
        Get,
        List
    }

    public static CollectionHandler Create(string collectionName, int vectorSize, QdrantDistanceType distanceType = QdrantDistanceType.Cosine)
    {
        return new CollectionHandler(collectionName, distanceType, vectorSize);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }

    internal QdrantResponse CreateQdrantCollection()
    {
        this.Validate();
        HttpRequest.CreatePutRequest(QdrantApiUrlConstants.CreateCollectionUrl(this._collectionName), payload: this); 

            
    }

    //TODO: Implement Get and List
    public object? Build(CollectionHandlerType requestType) 
    {
        this.Validate();

        switch (requestType)
        {
            case CollectionHandlerType.Create:
                var result = CreateQdrantCollection();
                return result;
            case CollectionHandlerType.Get:
                return HttpRequest.CreateGetRequest(QdrantApiUrlConstants.GetCollectionUrl(this._collectionName));
            case CollectionHandlerType.List:
                return HttpRequest.CreateGetRequest(QdrantApiUrlConstants.ListCollectionsUrl());
            default:
                throw new ArgumentOutOfRangeException(nameof(requestType), requestType, null);
        }
    }
        

    #region private ================================================================================

    private readonly string _collectionName;
    private readonly VectorSettings Settings;
    

    private CollectionHandler(string collectionName, QdrantDistanceType distanceType, int vectorSize)
    {
        this._collectionName = collectionName;
        this.Settings = new VectorSettings();
        this.Settings.DistanceType = distanceType;
        this.Settings.Size = vectorSize;

    }

    #endregion
}