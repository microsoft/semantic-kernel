namespace SKWebApi.Storage;

public class Repository<T> : IRepository<T> where T : IStorageEntity
{
    protected IStorageContext<T> _StorageContext;

    public Repository(IStorageContext<T> storageContext)
    {
        _StorageContext = storageContext;
    }

    public Task Create(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException("Invalid id.");
        }

        return _StorageContext.Create(entity);
    }

    public Task Delete(T entity)
    {
        return _StorageContext.Delete(entity);
    }

    public Task<T> FindById(string id)
    {
        return _StorageContext.Read(id);
    }

    public Task<IEnumerable<T>> FindAll()
    {
        return _StorageContext.FindAll();
    }

    public Task Update(T entity)
    {
        return _StorageContext.Update(entity);
    }
}
