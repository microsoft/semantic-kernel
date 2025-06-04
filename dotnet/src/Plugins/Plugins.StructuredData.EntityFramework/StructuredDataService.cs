// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data.Entity;
using System.Data.Entity.Infrastructure;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Community.OData.Linq;

#pragma warning disable CA1308 // Normalize strings to uppercase

namespace Microsoft.SemanticKernel;

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
        Verify.NotNull(dbContext);

        this.Context = dbContext;
    }

    /// <summary>
    /// Provides a queryable result set for the specified entity.
    /// </summary>
    /// <remarks>
    /// The search to the database is deferred until the query is enumerated.
    /// </remarks>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="query">Query string to filter entities.</param>
    public IQueryable<TEntity> Select<TEntity>(string? query = null)
        where TEntity : class
    {
        var result = this.Context.Set<TEntity>().AsQueryable();

        if (!string.IsNullOrWhiteSpace(query))
        {
            result = result.OData().Filter(query);
        }

        return result;
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
        Verify.NotNull(entity);

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
        Verify.NotNull(entity);

        try
        {
            var entry = this.Context.Entry(entity);
            if (entry.State == EntityState.Detached)
            {
                // Get primary key values from the entity
                var objectContext = ((IObjectContextAdapter)this.Context).ObjectContext;
                var objectSet = objectContext.CreateObjectSet<TEntity>();
                var keyNames = objectSet.EntitySet.ElementType.KeyMembers.Select(k => k.Name).ToArray();
                var keyValues = keyNames.Select(k => entry.Property(k).CurrentValue).ToArray();

                // Try to find existing entity with same key
                var existingEntity = this.Context.Set<TEntity>().Find(keyValues);
                if (existingEntity != null)
                {
                    // If entity exists, update its values
                    this.Context.Entry(existingEntity).CurrentValues.SetValues(entity);
                }
                else
                {
                    // If no existing entity, attach and mark as modified
                    this.Context.Set<TEntity>().Attach(entity);
                    entry.State = EntityState.Modified;
                }
            }

            return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error updating entity: {e.Message}");
            throw new InvalidOperationException($"Failed to update entity: {e.Message}", e);
        }
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
        Verify.NotNull(entity);
        try
        {
            var entry = this.Context.Entry(entity);
            if (entry.State == EntityState.Detached)
            {
                // Get primary key values from the entity
                var objectContext = ((IObjectContextAdapter)this.Context).ObjectContext;
                var objectSet = objectContext.CreateObjectSet<TEntity>();
                var keyNames = objectSet.EntitySet.ElementType.KeyMembers.Select(k => k.Name).ToArray();
                var keyValues = keyNames.Select(k => entry.Property(k).CurrentValue).ToArray();

                // Try to find existing entity with same key
                var existingEntity = this.Context.Set<TEntity>().Find(keyValues);
                if (existingEntity is not null)
                {
                    this.Context.Set<TEntity>().Remove(existingEntity);
                }
                else
                {
                    // If no existing entity, attach and remove
                    this.Context.Set<TEntity>().Attach(entity);
                    this.Context.Set<TEntity>().Remove(entity);
                }
            }
            else
            {
                this.Context.Set<TEntity>().Remove(entity);
            }
            return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error deleting entity: {e.Message}");
            throw new InvalidOperationException($"Failed to delete entity: {e.Message}", e);
        }
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
