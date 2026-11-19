// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Entity;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Factory class for creating Semantic Kernel plugins that enable structured data operations.
/// </summary>
public static class StructuredDataPluginFactory
{
    /// <summary>
    /// Creates a plugin that enables structured data operations for the specified entity type.
    /// </summary>
    /// <typeparam name="TContext">The type of DbContext to use for database operations.</typeparam>
    /// <typeparam name="TEntity">The entity type to perform operations on.</typeparam>
    /// <param name="service">The structured data service instance to use.</param>
    /// <param name="operations">Optional collection of operations to support. Defaults to query-only operations if not specified.</param>
    /// <param name="description">Optional description for the plugin. If not provided, a default description will be generated.</param>
    /// <returns>A KernelPlugin instance configured for the specified entity type and operations.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the specified operation is not supported by the service.</exception>
    /// <exception cref="NotSupportedException">
    /// Thrown if a mutation operation is requested without the explicit mapping and scoped resolution required by the safe mutation APIs.
    /// </exception>
    public static KernelPlugin CreateStructuredDataPlugin<TContext, TEntity>(
        StructuredDataService<TContext> service,
        IEnumerable<StructuredDataOperation>? operations = null,
        string? description = null)
        where TContext : DbContext
        where TEntity : class
    {
        operations ??= StructuredDataOperation.Default;
        description ??= $"Allows queries against the {typeof(TEntity).Name} entity in the database";

        var functions = new List<KernelFunction>();

        foreach (var operation in operations)
        {
            if (operation == StructuredDataOperation.Select)
            {
                functions.Add(service.CreateSelectFunction<TContext, TEntity>());
                continue;
            }

            if (operation == StructuredDataOperation.Insert ||
                operation == StructuredDataOperation.Update ||
                operation == StructuredDataOperation.Delete)
            {
                // Mutation functions need application-owned request mapping and row scope, which this convenience factory cannot infer.
                throw new NotSupportedException(
                    $"Operation '{operation}' requires an explicitly created safe mutation function. " +
                    $"Create it with a separate request type, then compose the plugin with {nameof(KernelPluginFactory)}.");
            }

            throw new InvalidOperationException($"Operation '{operation}' is not supported.");
        }

        return KernelPluginFactory.CreateFromFunctions(
            $"{typeof(TEntity).Name}DatabasePlugin",
            description,
            functions);
    }
}
