using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

public class CollectionHandler : IValidatable
{
    public enum CollectionHandlerType
    {
        Create,
        CheckExists,
        GetInfo,
        List,
        Delete
    }

    public static CollectionHandler Init(int vectorSize, QdrantDistanceType distanceType = QdrantDistanceType.Cosine)
    {
        return new CollectionHandler(distanceType, vectorSize);
    }

    public void Validate()
    {
        Verify.GreaterThan(this._settings.Size, 0, "The vector size must be greater than zero");
    }

    public CollectionHandler Client(HttpClient client)
    {
        this._client = client;
        Verify.NotNull(this._client, "The client must be defined");

        return this;
    }

    public CollectionHandler Build()
    {
        this.Validate();

        return this;
    }

    public async Task<IQdrantResult> ExecuteRequest(CollectionHandlerType requestType, string? collectionName = null)
    {
        IQdrantResult? qdrantResult = null;

        qdrantResult = requestType switch
        {
            CollectionHandlerType.CheckExists => 
                await this.CheckCollectionExistsAsync(collectionName!),
            CollectionHandlerType.GetInfo =>
                await this.GetCollectionInfoAsync(collectionName!),
            CollectionHandlerType.Create =>
                await this.CreateQdrantCollectionAsync(collectionName!),
            CollectionHandlerType.List =>
                await this.ListCollectionsAsync(),
            CollectionHandlerType.Delete =>
                await this.DeleteCollectionAsync(collectionName!),
            _ => throw new ArgumentOutOfRangeException(nameof(requestType), requestType, "The request type is not invalid")
                
        };

        return qdrantResult!;
    }

    public async Task<IQdrantResult> CheckCollectionExistsAsync(string collectionName)
    {
        IQdrantResult? qdrantCheckResult = null;
        string getURL = QdrantApiUrlConstants.GetCollectionUrl(collectionName);

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");

        

        return qdrantCheckResult!;
    }

    internal async Task<IQdrantResult> GetCollectionInfoAsync(string collectionName)
    {
        IQdrantResult? qdrantCollectionResult = null;
        string getURL = QdrantApiUrlConstants.GetCollectionUrl(collectionName);

        Verify.NotNullOrEmpty(collectionName, "The collection name must be defined");

        

        return qdrantCollectionResult!;

    }

    internal async Task<IQdrantResult> CreateQdrantCollectionAsync(string collectionName)
    {
        IQdrantResult? qdrantResult = null;

        string qdrantCreateUrl = QdrantApiUrlConstants.CreateCollectionUrl(collectionName);

        this.Validate();

        qdrantResult = await HttpRequest.SendHttpFromJsonAsync<CreateCollectionResult, VectorSettings>(
                        this._client,
                        HttpMethod.Put,
                        qdrantCreateUrl,
                        this._settings, null);

        return qdrantResult!;
    }

    internal async Task<IQdrantResult> ListCollectionsAsync()
    {
        IQdrantResult? qdrantResult = null;
       
        string qdrantListUrl = QdrantApiUrlConstants.GetCollectionsNamesUrl();

        qdrantResult = await HttpRequest.SendHttpFromJsonAsync<ListInfoResult, IQdrantResult>(
                    this._client,
                    HttpMethod.Get,
                    qdrantListUrl, null, null);

        return qdrantResult!;
    }

    internal async Task<IQdrantResult> DeleteCollectionAsync(string collectionName)
    {

        IQdrantResult? qdrantResult = null;

        string qdrantListUrl = QdrantApiUrlConstants.DeleteCollectionUrl(collectionName);

        qdrantResult = await HttpRequest.SendHttpFromJsonAsync<DeleteCollectionResult, IQdrantResult>(
                    this._client,
                    HttpMethod.Delete,
                    qdrantListUrl, null, null);
        
        return qdrantResult!;

    }


    #region private ================================================================================

    private VectorSettings _settings;

    private HttpClient _client;

    private CollectionHandler(QdrantDistanceType distanceType, int vectorSize)
    {
        this._settings = new VectorSettings();
        this._settings.DistanceType = distanceType;
        this._settings.Size = vectorSize;
    }

    #endregion
}

