// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using System.Linq.Expressions;

namespace StructuredDataConnector;

/// <summary>
/// Provides a structured data service for a database context.
/// </summary>
/// <typeparam name="TContext">Database context type.</typeparam>
public class StructuredDataService<TContext> : IDisposable where TContext : DbContext
{
    /// <summary>
    /// Gets the database context.
    /// </summary>
    public TContext Context { get; }

    /// <summary>
    /// Initializes a new instance with a connection string.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    public StructuredDataService(string connectionString)
    {
        this.Context = (TContext)Activator.CreateInstance(typeof(TContext), connectionString)!;
        this._internalContext = true;
    }

    /// <summary>
    /// Initializes a new instance with an existing DbContext.
    /// </summary>
    /// <param name="dbContext">The database context.</param>
    public StructuredDataService(TContext dbContext)
    {
        this.Context = dbContext
            ?? throw new ArgumentNullException(nameof(dbContext));
    }

    /// <summary>
    /// Provides a queryable result set for the specified entity.
    /// </summary>
    /// <remarks>
    /// The search to the database is deferred until the query is enumerated.
    /// </remarks>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="expression">Expression to filter entities.</param>
    public IQueryable<TEntity> Select<TEntity>(Expression<Func<TEntity, bool>>? expression = null)
        where TEntity : class
    {
        expression ??= (entity) => true;

        return this.Context.Set<TEntity>().Where(expression);
    }

    /// <summary>
    /// Inserts an entity and returns it with any generated values.
    /// </summary>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="entity">The entity to insert.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The inserted entity.</returns>
    public async Task<TEntity> InsertAsync<TEntity>(TEntity entity, CancellationToken cancellationToken = default) where TEntity : class
    {
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

        this.Context.Set<TEntity>().Add(entity);
        await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);

        return entity;
    }

    /// <summary>
    /// Updates an entity and returns the number of affected rows.
    /// </summary>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="entity">The entity to update.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The number of affected rows.</returns>
    public async Task<int> UpdateAsync<TEntity>(TEntity entity, CancellationToken cancellationToken = default) where TEntity : class
    {
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

        var entry = this.Context.Entry(entity);
        if (entry.State == EntityState.Detached)
        {
            this.Context.Set<TEntity>().Attach(entity);
            entry.State = EntityState.Modified;
        }

        return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Deletes an entity and returns the number of affected rows.
    /// </summary>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="entity">The entity to delete.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The number of affected rows.</returns>
    public async Task<int> DeleteAsync<TEntity>(TEntity entity, CancellationToken cancellationToken = default) where TEntity : class
    {
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

        var entry = this.Context.Entry(entity);
        if (entry.State == EntityState.Detached)
        {
            this.Context.Set<TEntity>().Attach(entity);
        }
        this.Context.Set<TEntity>().Remove(entity);

        return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Disposes resources used by the service.
    /// </summary>
    protected virtual void Dispose(bool disposing)
    {
        if (this._disposed)
        {
            return;
        }

        if (disposing && this._internalContext)
        {
            this.Context.Dispose();
        }

        this._disposed = true;
    }

    /// <summary>
    /// Disposes the context if it was created internally.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    private readonly bool _internalContext;
    private bool _disposed;
}
