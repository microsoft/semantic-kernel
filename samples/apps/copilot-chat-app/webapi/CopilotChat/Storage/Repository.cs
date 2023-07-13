// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// Defines the basic CRUD operations for a repository.
/// </summary>
public class Repository<T> : IRepository<T> where T : IStorageEntity
{
    /// <summary>
    /// The storage context.
    /// </summary>
    protected IStorageContext<T> StorageContext { get; set; }

    /// <summary>
    /// Initializes a new instance of the Repository class.
    /// </summary>
    public Repository(IStorageContext<T> storageContext)
    {
        this.StorageContext = storageContext;
    }

    /// <inheritdoc/>
    public Task CreateAsync(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException(nameof(entity.Id), "Entity Id cannot be null or empty.");
        }

        return this.StorageContext.CreateAsync(entity);
    }

    /// <inheritdoc/>
    public Task DeleteAsync(T entity)
    {
        return this.StorageContext.DeleteAsync(entity);
    }

    /// <inheritdoc/>
    public Task<T> FindByIdAsync(string id)
    {
        return this.StorageContext.ReadAsync(id);
    }

    /// <inheritdoc/>
    public async Task<bool> TryFindByIdAsync(string id, Action<T?> entity)
    {
        try
        {
            entity(await this.FindByIdAsync(id));
            return true;
        }
        catch (Exception ex) when (ex is ArgumentOutOfRangeException || ex is KeyNotFoundException)
        {
            entity(default);
            return false;
        }
    }

    /// <inheritdoc/>
    public Task UpsertAsync(T entity)
    {
        return this.StorageContext.UpsertAsync(entity);
    }
}
