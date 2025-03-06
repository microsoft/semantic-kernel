// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using Microsoft.SemanticKernel;

namespace StructuredDataConnector;

/// <summary>
/// Extension methods for <see cref="StructuredDataService{TContext}"/>.
/// </summary>
public static class StructuredDataServiceExtensions
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> from the entity insertion method.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity insertion.</returns>
    public static KernelFunction CreateInsertFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Insert{typeof(TEntity).Name}Record",
            Description = "Insert the provided entity record into the database.",
            Parameters =
            [
                new KernelParameterMetadata("entity") { Description = "Entity record information", IsRequired = true },
            ],
            ReturnParameter = new() { ParameterType = typeof(TEntity) },
        };

        async Task<TEntity> InsertAsync(TEntity entity, CancellationToken cancellationToken)
        {
            return await service.InsertAsync(entity, cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(InsertAsync, options);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> from the entity insertion method.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity insertion.</returns>
    public static KernelFunction CreateSelectFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Select{typeof(TEntity).Name}Records",
            Description = $"Gets {typeof(TEntity).Name} records from the database.",
            Parameters = [],
            ReturnParameter = new() { ParameterType = typeof(IList<TEntity>) },
        };

        async Task<IList<TEntity>> SelectAsync(CancellationToken cancellationToken)
        {
            return await service.Select<TEntity>().ToListAsync().ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(SelectAsync, options);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> from the entity update method.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity update.</returns>
    public static KernelFunction CreateUpdateFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Update{typeof(TEntity).Name}Record",
            Description = "Update the provided entity record in the database.",
            Parameters =
            [
                new KernelParameterMetadata("entity") { Description = "Entity record information to update", IsRequired = true },
            ],
            ReturnParameter = new() { ParameterType = typeof(int), Description = "Number of affected rows" },
        };

        async Task<int> UpdateAsync(TEntity entity, CancellationToken cancellationToken)
        {
            return await service.UpdateAsync(entity, cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(UpdateAsync, options);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> from the entity delete method.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity deletion.</returns>
    public static KernelFunction CreateDeleteFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Delete{typeof(TEntity).Name}Record",
            Description = "Delete the provided entity record from the database.",
            Parameters =
            [
                new KernelParameterMetadata("entity") { Description = "Entity record to delete", IsRequired = true },
            ],
            ReturnParameter = new() { ParameterType = typeof(int), Description = "Number of affected rows" },
        };

        async Task<int> DeleteAsync(TEntity entity, CancellationToken cancellationToken)
        {
            return await service.DeleteAsync(entity, cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(DeleteAsync, options);
    }
}
