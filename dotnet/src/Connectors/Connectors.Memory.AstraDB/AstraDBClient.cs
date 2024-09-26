using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;


namespace Microsoft.SemanticKernel.Connectors.AstraDB
{
  /// <summary>
  /// This class implements Astra DB API operations.
  /// </summary>
  public class AstraDBClient : IAstraDBClient
  {
    /// <summary>
    /// Initializes a new instance of the <see cref="AstraDBClient"/> class.
    /// </summary>
    /// <param name="apiEndpoint">API endpoint of Astra DB.</param>
    /// <param name="appToken">Application token for Astra DB. Ensure to create a token with correct role permissions.</param>
    /// <param name="keySpace">Name of the keyspace you want to work with.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    public AstraDBClient(string apiEndpoint, string appToken, string keySpace, int vectorSize)
    {
      _apiEndpoint = apiEndpoint;
      _appToken = appToken;
      _keySpace = keySpace;
      _vectorSize = vectorSize;
      _httpClient = HttpClientProvider.GetHttpClient();
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var jsonContent = $@"
            {{
                ""createCollection"": {{
                    ""name"": ""{collectionName}"",
                    ""options"": {{
                        ""vector"": {{
                            ""size"": {_vectorSize},
                            ""function"": ""cosine""
                        }}
                    }}
                }}
            }}";

      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
      await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var jsonContent = "{\n  \"findCollections\": {}\n}";
      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
      response.EnsureSuccessStatusCode();

      using (var responseStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false))
      {
        var jsonDocument = await JsonDocument.ParseAsync(responseStream, cancellationToken: cancellationToken).ConfigureAwait(false);
        var collectionsArray = jsonDocument.RootElement.GetProperty("status").GetProperty("collections").EnumerateArray();

        foreach (var collection in collectionsArray)
        {
          yield return collection.GetString();
        }
      }
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var jsonPayload = new
      {
        deleteCollection = new
        {
          name = collectionName
        }
      };

      var jsonContent = JsonSerializer.Serialize(jsonPayload);
      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
      response.EnsureSuccessStatusCode();
    }

    /// <inheritdoc />
    public async Task UpsertAsync(string collectionName, string key, string? metadata, float[]? embedding, CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}/{collectionName}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var document = new Dictionary<string, object>
      {
        { "id", key },
        { "metadata", metadata },
        { "$vector", embedding },
    };
      var jsonContent = new
      {
        insertOne = new
        {
          document
        }
      };

      var contentString = JsonSerializer.Serialize(jsonContent);
      var content = new StringContent(contentString, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
      await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> FindOneAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}/{collectionName}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var jsonContent = $@"
                {{
                    ""findOne"": {{
                        ""filter"": {{ ""id"": ""{key}"" }},
                        ""projection"": {{ ""$vector"": 1 }}
                    }}
                }}";
      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

      if (response.IsSuccessStatusCode)
      {
        var responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        var document = JsonSerializer.Deserialize<AstraDBMemoryResponse>(responseContent);

        if (document?.Data?.Document != null)
        {
          var metadata = MemoryRecord.FromJsonMetadata(
                json: document.Data.Document.MetadataString,
                embedding: document.Data.Document.Vector?.ToArray() ?? Array.Empty<float>(), // Adjust if embedding is provided
                key: document.Data.Document.Id,
                timestamp: null // Assuming no timestamp is available
            );
          return metadata;
        }
      }
      return null;
    }

    /// <inheritdoc />
    public async Task DeleteOneAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}/{collectionName}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var jsonContent = $@"
    {{
        ""deleteOne"": {{
            ""filter"": {{ ""id"": ""{key}"" }}
        }}
    }}";

      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
      response.EnsureSuccessStatusCode();
    }

    /// <inheritdoc />
    public async Task DeleteManyAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
      const int MaxBatchSize = 20;
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}/{collectionName}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);

      var keysList = keys.ToList();

      for (int currentIndex = 0; currentIndex < keysList.Count; currentIndex += MaxBatchSize)
      {
        var batch = keysList.Skip(currentIndex).Take(MaxBatchSize).ToList();
        var keyArray = string.Join("\",\"", batch);
        var jsonContent = $@"
        {{
            ""deleteMany"": {{
                ""filter"": {{ 
                    ""id"": {{
                        ""$in"": [""{keyArray}""]
                    }}
                }}
            }}
        }}";

        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

        request.Content = content;

        var response = await _httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
      }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(AstraDBMemoryEntry, double)> GetNearestMatchesAsync(
       string collectionName,
       ReadOnlyMemory<float> embedding,
       int limit,
       double minRelevanceScore = 0,
       bool withEmbeddings = false,
       [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
      var requestUrl = $"{GetApiBaseUrl()}/{_keySpace}/{collectionName}";

      var request = new HttpRequestMessage(HttpMethod.Post, requestUrl);
      request.Headers.Add("x-cassandra-token", _appToken);
      var projection = withEmbeddings ? "\"$vector\": 1" : "";
      var jsonContent = $@"
    {{
        ""find"": {{
            ""sort"": {{ ""$vector"": [{string.Join(", ", embedding.ToArray())}] }},
            ""projection"": {{ {projection} }},
            ""options"": {{
                ""includeSimilarity"": true,
                ""limit"": {limit}
            }}
        }}
    }}";
      var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
      request.Content = content;

      var response = await _httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
      response.EnsureSuccessStatusCode();

      var responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

      var astraDBResponse = JsonSerializer.Deserialize<AstraDBNearestMatchesResponse>(responseContent);

      if (astraDBResponse?.Data?.Documents != null)
      {
        foreach (var document in astraDBResponse.Data.Documents)
        {
          if (document.Similarity >= minRelevanceScore)
          {
            yield return (new AstraDBMemoryEntry
            {
              Id = document.Id,
              MetadataString = document.Metadata,
              Vector = withEmbeddings ? document.Vector.ToArray() : null,
              Similarity = document.Similarity
            }, document.Similarity);
          }
        }
      }
    }

    #region Private Fields

    private readonly string _apiEndpoint;
    private readonly string _appToken;
    private readonly string _keySpace;
    private readonly HttpClient _httpClient;
    private readonly int _vectorSize;

    private string GetApiBaseUrl()
    {
      return $"{_apiEndpoint}/api/json/v1";
    }

    #endregion
  }
}
