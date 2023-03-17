using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
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
        List, 
        Delete
    }

    public static CollectionHandler Create(string collectionName, int vectorSize, QdrantDistanceType distanceType = QdrantDistanceType.Cosine)
    {
        return new CollectionHandler(collectionName, distanceType, vectorSize);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }

    internal async Task<CollectionData> CreateQdrantCollectionAsync()
    {
        CollectionData response = null!;
        string qdrantCreateUrl = QdrantApiUrlConstants.CreateCollectionUrl(this._collectionName);

        this.Validate();
        //HttpRequest.CreatePutRequest(qdrantCreateUrl, payload: this); 
        
        response = await HttpRequest.SendHttpFromJsonAsync<VectorSettings, CollectionData>(
                            this._client, 
                            HttpMethod.Put, 
                            qdrantCreateUrl, 
                            this._settings);
        return response!;
            
    }

    public CollectionHandler Client(HttpClient client)
    {
        this._client = client;
        return this;
    }
    
    //TODO: Implement Get, List, Delete
    //TODO: Implement Generic for Build prevent boxing
    public async Task<object> Build(CollectionHandlerType requestType) 
    {
        object responseHold = null!;

        this.Validate();

        switch (requestType)
        {
            case CollectionHandlerType.Create:
                var result = await CreateQdrantCollectionAsync();
                responseHold = (CollectionData)result; 
                break;

            case CollectionHandlerType.Get:
                //HttpRequest.CreateGetRequest(QdrantApiUrlConstants.GetCollectionUrl(this._collectionName));
                break;

            case CollectionHandlerType.List:
                //HttpRequest.CreateGetRequest(QdrantApiUrlConstants.ListCollectionsUrl());
                break;

            case CollectionHandlerType.Delete:
                break;

            default:
                throw new ArgumentOutOfRangeException(nameof(requestType), requestType, null);
        }

        return responseHold;
    }
        

    #region private ================================================================================

    private string _collectionName;
    private VectorSettings _settings;
    
    private HttpClient _client;
    

    private CollectionHandler(string collectionName, QdrantDistanceType distanceType, int vectorSize)
    {
        this._collectionName = collectionName;
        this._settings = new VectorSettings();
        this._settings.DistanceType = distanceType;
        this._settings.Size = vectorSize;

    }

    #endregion
}