using Microsoft.Azure.Cosmos;

namespace SKWebApi.Storage;

public class CosmosDbContext<T> : IStorageContext<T> where T : IStorageEntity
{
    private readonly CosmosClient _client;
    private readonly Container _container;

    public CosmosDbContext(string connectionString, string database, string container)
    {
        this._client = new CosmosClient(connectionString);
        this._container = this._client.GetContainer(database, container);
    }

    public IQueryable<T> QueryableEntities => this._container.GetItemLinqQueryable<T>().AsQueryable();

    public async Task Create(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        await this._container.CreateItemAsync(entity);
    }

    public async Task Delete(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        await this._container.DeleteItemAsync<T>(entity.Id, new PartitionKey(entity.Id));
    }

    public async Task<IEnumerable<T>> FindAll()
    {
        var query = this._container.GetItemQueryIterator<T>();
        var results = new List<T>();

        while (query.HasMoreResults)
        {
            var response = await query.ReadNextAsync();
            results.AddRange(response);
        }

        return results;
    }

    public async Task<T?> Read(string entityId)
    {
        if (string.IsNullOrWhiteSpace(entityId))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        try
        {
            var response = await this._container.ReadItemAsync<T>(entityId, new PartitionKey(entityId));
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return default;
        }
    }

    public async Task Update(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        await this._container.UpsertItemAsync(entity);
    }
}

