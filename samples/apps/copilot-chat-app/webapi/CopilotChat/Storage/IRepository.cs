// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// Defines the basic CRUD operations for a repository.
/// </summary>
public interface IRepository<T> where T : IStorageEntity
{
    /// <summary>
    /// Creates a new entity in the repository.
    /// </summary>
    /// <param name="entity">An entity of type T.</param>
    Task CreateAsync(T entity);

    /// <summary>
    /// Deletes an entity from the repository.
    /// </summary>
    /// <param name="entity">The entity to delete.</param>
    Task DeleteAsync(T entity);

    /// <summary>
    /// Upserts an entity in the repository.
    /// </summary>
    /// <param name="entity">The entity to be upserted.</param>
    Task UpsertAsync(T entity);

    /// <summary>
    /// Finds an entity by its id.
    /// </summary>
    /// <param name="id">Id of the entity.</param>
    /// <returns>An entity</returns>
    Task<T> FindByIdAsync(string id);

    /// <summary>
    /// Tries to find an entity by its id.
    /// </summary>
    /// <param name="id">Id of the entity.</param>
    /// <param name="entity">The entity delegate. Note async methods don't support ref or out parameters.</param>
    /// <returns>True if the entity was found, false otherwise.</returns>
    Task<bool> TryFindByIdAsync(string id, Action<T?> entity);
}
