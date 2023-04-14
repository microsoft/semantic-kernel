namespace SKWebApi.Storage;

/// <summary>
/// Defines the basic CRUD operations for a repository.
/// </summary>
public class Repository<T> : IRepository<T> where T : IStorageEntity
{
    /// <summary>
    /// The storage context.
    /// </summary>
    protected IStorageContext<T> storageContext { get; set; }

    /// <summary>
    /// Initializes a new instance of the Repository class.
    /// </summary>
    public Repository(IStorageContext<T> storageContext)
    {
        this.storageContext = storageContext;
    }

    /// <inheritdoc/>
    public Task CreateAsync(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException(nameof(entity.Id), "Entity Id cannot be null or empty.");
        }

        return this.storageContext.CreateAsync(entity);
    }

    /// <inheritdoc/>
    public Task DeleteAsync(T entity)
    {
        return this.storageContext.DeleteAsync(entity);
    }

    /// <inheritdoc/>
    public Task<T> FindByIdAsync(string id)
    {
        return this.storageContext.ReadAsync(id);
    }

    /// <inheritdoc/>
    public Task UpdateAsync(T entity)
    {
        return this.storageContext.UpdateAsync(entity);
    }
}
