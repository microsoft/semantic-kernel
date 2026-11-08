// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Entity;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="StructuredDataService{TContext}"/>.
/// </summary>
public static class StructuredDataServiceExtensions
{
    /// <summary>
    /// Legacy insertion overload that accepted a persistence entity directly.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>This method does not return.</returns>
    /// <exception cref="NotSupportedException">
    /// Always thrown because binding model input directly to a persistence entity does not provide a safe mutation boundary.
    /// </exception>
    public static KernelFunction CreateInsertFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        throw new NotSupportedException(DirectEntityMutationNotSupportedMessage);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> that maps a separate input type to an entity before insertion.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <typeparam name="TInput">The model-visible insertion request type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="mapInput">Application-controlled mapping from model input to a persistence entity.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity insertion.</returns>
    /// <exception cref="NotSupportedException">
    /// Thrown when <typeparamref name="TInput"/> is the entity type or belongs to the same inheritance hierarchy.
    /// </exception>
    public static KernelFunction CreateInsertFunction<TContext, TEntity, TInput>(
        this StructuredDataService<TContext> service,
        Func<TInput, TEntity> mapInput,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
        where TInput : class
    {
        Verify.NotNull(service);
        Verify.NotNull(mapInput);
        EnsureSeparateInputType<TInput, TEntity>();

        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Insert{typeof(TEntity).Name}Record",
            Description = $"Insert a {typeof(TEntity).Name} record into the database.",
            Parameters =
            [
                new KernelParameterMetadata("input")
                {
                    ParameterType = typeof(TInput),
                    Schema = KernelJsonSchemaBuilder.Build(typeof(TInput)),
                    Description = "Information for the record to insert",
                    IsRequired = true
                },
            ],
            ReturnParameter = new() { ParameterType = typeof(TEntity) },
        };

        async Task<TEntity> InsertAsync(TInput input, CancellationToken cancellationToken)
        {
            // Only the application mapper may create the persistence entity, so model input cannot set unexposed members.
            var entity = mapInput(input);
            Verify.NotNull(entity);
            return await service.InsertAsync(entity, cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(InsertAsync, options);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> from the entity select method.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity selection.</returns>
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
            Parameters =
            [
                new KernelParameterMetadata("filter")
                {
                    ParameterType = typeof(string),
                    Description = string.Concat($"A ODATA filter expression to query {typeof(TEntity).Name}.",
                        "Supported operators: ",
                        "'gt' (greater than), ",
                        "'lt' (less than), ",
                        "'eq' (equals), ",
                        "'contains' (string contains), ",
                        "'startswith' (string starts with), ",
                        "'endswith' (string ends with), ",
                        "Combine with 'and', 'or'. ",
                        "Wrap string values in single quotes."),
                    IsRequired = false
                },
            ],
            ReturnParameter = new() { ParameterType = typeof(IList<TEntity>) },
        };

        Task<IList<TEntity>> Select(string? filter = null, CancellationToken cancellationToken = default)
            => Task.FromResult<IList<TEntity>>(service.Select<TEntity>(filter).ToList());

        return KernelFunctionFactory.CreateFromMethod(Select, options);
    }

    /// <summary>
    /// Legacy update overload that accepted a persistence entity directly.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>This method does not return.</returns>
    /// <exception cref="NotSupportedException">
    /// Always thrown because binding model input directly to a persistence entity does not provide a safe mutation boundary.
    /// </exception>
    public static KernelFunction CreateUpdateFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        throw new NotSupportedException(DirectEntityMutationNotSupportedMessage);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> that resolves an authorized entity and applies an explicit update mapping.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <typeparam name="TInput">The model-visible update request type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="resolveEntity">
    /// Application-controlled resolver that applies the caller's row scope and returns an entity tracked by
    /// <paramref name="service"/>.
    /// </param>
    /// <param name="applyUpdates">Application-controlled mapping of allowed input members to the resolved entity.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity update.</returns>
    /// <exception cref="NotSupportedException">
    /// Thrown when <typeparamref name="TInput"/> is the entity type or belongs to the same inheritance hierarchy.
    /// </exception>
    /// <exception cref="InvalidOperationException">
    /// Thrown during invocation when the resolver does not return an entity tracked by <paramref name="service"/>.
    /// </exception>
    public static KernelFunction CreateUpdateFunction<TContext, TEntity, TInput>(
        this StructuredDataService<TContext> service,
        Func<TInput, CancellationToken, Task<TEntity?>> resolveEntity,
        Action<TInput, TEntity> applyUpdates,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
        where TInput : class
    {
        Verify.NotNull(service);
        Verify.NotNull(resolveEntity);
        Verify.NotNull(applyUpdates);
        EnsureSeparateInputType<TInput, TEntity>();

        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Update{typeof(TEntity).Name}Record",
            Description = $"Update a {typeof(TEntity).Name} record in the database.",
            Parameters =
            [
                new KernelParameterMetadata("input")
                {
                    ParameterType = typeof(TInput),
                    Schema = KernelJsonSchemaBuilder.Build(typeof(TInput)),
                    Description = "Information identifying the record and allowed updates",
                    IsRequired = true
                },
            ],
            ReturnParameter = new() { ParameterType = typeof(int), Description = "Number of affected rows" },
        };

        async Task<int> UpdateAsync(TInput input, CancellationToken cancellationToken)
        {
            // The resolver is the row-authorization boundary and must use this context so the entity cannot be swapped later.
            var entity = await resolveEntity(input, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidOperationException("The requested entity is not available for update.");

            if (service.Context.Entry(entity).State == EntityState.Detached)
            {
                throw new InvalidOperationException("The update resolver must return an entity tracked by the structured data service.");
            }

            // Only explicitly mapped request members may change server-managed entity state.
            applyUpdates(input, entity);
            return await service.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(UpdateAsync, options);
    }

    /// <summary>
    /// Legacy deletion overload that accepted a persistence entity directly.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>This method does not return.</returns>
    /// <exception cref="NotSupportedException">
    /// Always thrown because binding model input directly to a persistence entity does not provide a safe mutation boundary.
    /// </exception>
    public static KernelFunction CreateDeleteFunction<TContext, TEntity>(
        this StructuredDataService<TContext> service,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
    {
        throw new NotSupportedException(DirectEntityMutationNotSupportedMessage);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> that resolves an authorized entity before deletion.
    /// </summary>
    /// <typeparam name="TContext">The database context type.</typeparam>
    /// <typeparam name="TEntity">The entity type.</typeparam>
    /// <typeparam name="TInput">The model-visible deletion request type.</typeparam>
    /// <param name="service">Structured data service.</param>
    /// <param name="resolveEntity">
    /// Application-controlled resolver that applies the caller's row scope and returns an entity tracked by
    /// <paramref name="service"/>.
    /// </param>
    /// <param name="options">Kernel function options.</param>
    /// <returns>Kernel function for entity deletion.</returns>
    /// <exception cref="NotSupportedException">
    /// Thrown when <typeparamref name="TInput"/> is the entity type or belongs to the same inheritance hierarchy.
    /// </exception>
    /// <exception cref="InvalidOperationException">
    /// Thrown during invocation when the resolver does not return an entity tracked by <paramref name="service"/>.
    /// </exception>
    public static KernelFunction CreateDeleteFunction<TContext, TEntity, TInput>(
        this StructuredDataService<TContext> service,
        Func<TInput, CancellationToken, Task<TEntity?>> resolveEntity,
        KernelFunctionFromMethodOptions? options = null)
        where TContext : DbContext
        where TEntity : class
        where TInput : class
    {
        Verify.NotNull(service);
        Verify.NotNull(resolveEntity);
        EnsureSeparateInputType<TInput, TEntity>();

        options ??= new KernelFunctionFromMethodOptions
        {
            FunctionName = $"Delete{typeof(TEntity).Name}Record",
            Description = $"Delete a {typeof(TEntity).Name} record from the database.",
            Parameters =
            [
                new KernelParameterMetadata("input")
                {
                    ParameterType = typeof(TInput),
                    Schema = KernelJsonSchemaBuilder.Build(typeof(TInput)),
                    Description = "Information identifying the record to delete",
                    IsRequired = true
                },
            ],
            ReturnParameter = new() { ParameterType = typeof(int), Description = "Number of affected rows" },
        };

        async Task<int> DeleteAsync(TInput input, CancellationToken cancellationToken)
        {
            // The resolver is the row-authorization boundary and must use this context so only an approved row is removed.
            var entity = await resolveEntity(input, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidOperationException("The requested entity is not available for deletion.");

            if (service.Context.Entry(entity).State == EntityState.Detached)
            {
                throw new InvalidOperationException("The deletion resolver must return an entity tracked by the structured data service.");
            }

            service.Context.Set<TEntity>().Remove(entity);
            return await service.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
        }

        return KernelFunctionFactory.CreateFromMethod(DeleteAsync, options);
    }

    private const string DirectEntityMutationNotSupportedMessage =
        "Direct persistence-entity arguments are not supported for structured data mutation functions. " +
        "Use the overload with a separate request type and application-controlled mapping or scoped entity resolution.";

    private static void EnsureSeparateInputType<TInput, TEntity>()
    {
        if (typeof(TEntity).IsAssignableFrom(typeof(TInput)) || typeof(TInput).IsAssignableFrom(typeof(TEntity)))
        {
            throw new NotSupportedException(
                $"The mutation input type '{typeof(TInput).Name}' must be separate from the persistence entity type '{typeof(TEntity).Name}'.");
        }
    }
}
