namespace SKWebApi.Storage;

public interface IStorageContext<T> where T : IStorageEntity
{
    IQueryable<T> QueryableEntities { get; }
    
    Task<IEnumerable<T>> FindAll();

    Task<T> Read(string entityId);

    Task Create(T entity);

    Task Update(T entity);

    Task Delete(T entity);
}
