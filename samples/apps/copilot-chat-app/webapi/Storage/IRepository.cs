namespace SKWebApi.Storage;

public interface IRepository<T> where T : IStorageEntity
{
    Task Create(T entity);

    Task Delete(T entity);

    Task Update(T entity);

    Task<T> FindById(string id);

    Task<IEnumerable<T>> FindAll();
}
