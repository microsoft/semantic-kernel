// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Azure.Cosmos;
using Newtonsoft.Json.Linq;

namespace PlayFabExamples.Example01_DataQnA.Reports;

public class ReportDataFetcher : IDisposable
{
    private readonly string _titleId;
    private readonly CosmosClient _cosmosClient;
    private readonly string _databaseName;
    private readonly string _containerName;

    public ReportDataFetcher(string titleId, string endpointUrl, string primaryKey, string databaseName, string containerName)
    {
        this._titleId = titleId ?? throw new ArgumentNullException(nameof(titleId));
        this._cosmosClient = new(
            endpointUrl ?? throw new ArgumentNullException(nameof(endpointUrl)),
            primaryKey ?? throw new ArgumentNullException(nameof(primaryKey)));

        this._databaseName = databaseName ?? throw new ArgumentNullException(nameof(databaseName));
        this._containerName = containerName ?? throw new ArgumentNullException(nameof(containerName));
    }

    public async Task<GameReport> FetchAsync(string documentId, CancellationToken cancellationToken)
    {
        // Get a reference to the database and container
        Database database = this._cosmosClient.GetDatabase(this._databaseName);
        Container container = database.GetContainer(this._containerName);

        // Read the document by its ID
        ItemResponse<GameReport> response = await container.ReadItemAsync<GameReport>(documentId, new PartitionKey(this._titleId), cancellationToken: cancellationToken);
        return response.Resource;
    }

    public async Task<IList<GameReport>> FetchByQueryAsync(string query, CancellationToken cancellationToken)
    {
        // Get a reference to the database and container
        Database database = this._cosmosClient.GetDatabase(this._databaseName);
        Container container = database.GetContainer(this._containerName);

        List<GameReport> ret = new();

        // Execute the query
        QueryDefinition queryDefinition = new(query);
        FeedIterator<dynamic> resultSetIterator = container.GetItemQueryIterator<dynamic>(queryDefinition);

        while (resultSetIterator.HasMoreResults)
        {
            FeedResponse<dynamic> response = await resultSetIterator.ReadNextAsync(cancellationToken);
            foreach (dynamic item in response)
            {
                GameReport? gameReport = ((JObject)item).ToObject<GameReport>();
                if (gameReport is not null)
                {
                    ret.Add(gameReport);
                }
            }
        }

        return ret;
    }

    public void Dispose()
    {
        this._cosmosClient.Dispose();
    }
}
