using System.Collections.Concurrent;

namespace SKWebApi.Storage;

public class InMemoryContext<T> : IStorageContext<T> where T : IStorageEntity
{
    private readonly ConcurrentDictionary<string, T> _entities;

    public InMemoryContext()
    {
        this._entities = new ConcurrentDictionary<string, T>();
    }

    public IQueryable<T> QueryableEntities => this._entities.Values.AsQueryable();

    public Task Create(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        this._entities.TryAdd(entity.Id, entity);

        return Task.CompletedTask;
    }

    public Task Delete(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        this._entities.TryRemove(entity.Id, out _);

        return Task.CompletedTask;
    }

    public Task<IEnumerable<T>> FindAll()
    {
        return Task.FromResult(this._entities.Values.AsEnumerable());
    }

    public Task<T> Read(string entityId)
    {
        if (string.IsNullOrWhiteSpace(entityId))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        if (this._entities.TryGetValue(entityId, out T? entity))
        {
            return Task.FromResult(entity);
        }
        else
        {
            throw new KeyNotFoundException($"Entity with id {entityId} not found.");
        }
    }

    public Task Update(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        this._entities.TryUpdate(entity.Id, entity, this._entities[entity.Id]);

        return Task.CompletedTask;
    }
}
