// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Storage;

/// <summary>
/// Defines the basic CRUD operations for a storage context.
/// </summary>
public interface IStorageContext<T> where T : IStorageEntity
{
    /// <summary>
    /// Queryable entities.
    /// </summary>
    IQueryable<T> QueryableEntities { get; }

    /// <summary>
    /// When true, the consumer of this storage context should handle queryable entities
    /// that are retrieved via a blocking operation with a Task.Run (or similar)
    /// </summary>
    bool IsQueryBlocking { get; }

    /// <summary>
    /// Read an entity from the storage context by id.
    /// </summary>
    /// <param name="entityId">The entity id.</param>
    /// <returns>The entity.</returns>
    Task<T> ReadAsync(string entityId);

    /// <summary>
    /// Create an entity in the storage context.
    /// </summary>
    /// <param name="entity">The entity to be created in the context.</param>
    Task CreateAsync(T entity);

    /// <summary>
    /// Update an entity in the storage context.
    /// </summary>
    /// <param name="entity">The entity to be updated in the context.</param>
    Task UpdateAsync(T entity);

    /// <summary>
    /// Delete an entity from the storage context.
    /// </summary>
    /// <param name="entity">The entity to be deleted from the context.</param>
    Task DeleteAsync(T entity);
}
