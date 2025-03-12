// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Entity;
using System.Reflection;

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
    /// <param name="operations">Optional collection of operations to support. Defaults to StructuredDataOperations.Default if not specified.</param>
    /// <param name="description">Optional description for the plugin. If not provided, a default description will be generated.</param>
    /// <returns>A KernelPlugin instance configured for the specified entity type and operations.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the specified operation is not supported by the service.</exception>
    public static KernelPlugin CreateStructuredDataPlugin<TContext, TEntity>(
        StructuredDataService<TContext> service,
        IEnumerable<StructuredDataOperation>? operations = null,
        string? description = null)
        where TContext : DbContext
        where TEntity : class
    {
        operations ??= StructuredDataOperation.Default;
        description ??= $"Allows CRUD operations against the {typeof(TEntity).Name} entity in the database";

        var functions = new List<KernelFunction>();
        var extensionsType = typeof(StructuredDataServiceExtensions);

        foreach (var operation in operations)
        {
            // Look for Create{Operation}Function method in the extensions
            var methodName = $"Create{operation}Function";
            var method = extensionsType.GetMethod(methodName, BindingFlags.Public | BindingFlags.Static);

            if (method == null)
            {
                throw new InvalidOperationException(
                    $"Operation '{operation}' is not supported. Extension method '{methodName}' not found.");
            }

            try
            {
                var genericMethod = method.MakeGenericMethod(typeof(TContext), typeof(TEntity));
                var function = (KernelFunction)genericMethod.Invoke(null, new object?[] { service, null })!;
                functions.Add(function);
            }
            catch (Exception ex) when (ex is not InvalidOperationException)
            {
                throw new InvalidOperationException(
                    $"Failed to create function for operation '{operation}': {ex.Message}", ex);
            }
        }

        return KernelPluginFactory.CreateFromFunctions(
            $"{typeof(TEntity).Name}DatabasePlugin",
            description,
            functions);
    }
}
