namespace SKWebApi.Storage;

public class Repository<T> : IRepository<T> where T : IStorageEntity
{
    protected IStorageContext<T> _StorageContext;

    public Repository(IStorageContext<T> storageContext)
    {
        this._StorageContext = storageContext;
    }

    public Task Create(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        return this._StorageContext.Create(entity);
    }

    public Task Delete(T entity)
    {
        return this._StorageContext.Delete(entity);
    }

    public Task<T> FindById(string id)
    {
        return this._StorageContext.Read(id);
    }

    public Task<IEnumerable<T>> FindAll()
    {
        return this._StorageContext.FindAll();
    }

    public Task Update(T entity)
    {
        return this._StorageContext.Update(entity);
    }
}
