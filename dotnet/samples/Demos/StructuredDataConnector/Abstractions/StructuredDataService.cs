// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using System.Linq.Expressions;

namespace StructuredDataConnector.Abstractions;

/// <summary>
/// Represents a connection to a data source.
/// </summary>
public class StructuredDataService<TContext> : IDisposable where TContext : DbContext
{
    /// <summary>
    /// Gets the database context.
    /// </summary>
    public TContext Context { get; }

    private readonly bool _internalContext;

    /// <summary>
    /// Initializes a new instance of the <see cref="StructuredDataService"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    public StructuredDataService(string connectionString)
    {
        this.Context = (TContext)Activator.CreateInstance(typeof(TContext), connectionString);
        this._internalContext = true;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StructuredDataService"/> class.
    /// </summary>
    /// <param name="dbContext">The database context.</param>
    public StructuredDataService(TContext dbContext)
    {
        this.Context = dbContext;
    }

    /// <summary>
    /// Releases the unmanaged resources used by the StructuredDataService and optionally releases the managed resources.
    /// </summary>
    /// <param name="disposing">true to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing && this._internalContext)
        {
            this.Context.Dispose();
        }
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Searches for entities that match the specified expression.
    /// </summary>
    /// <typeparam name="T">The entity type.</typeparam>
    /// <param name="expression">Expression to filter entities.</param>
    public virtual IQueryable<T> SearchByEntity<T>(Expression<Func<T, bool>> expression)
        where T : class
    {
        return this.Context.Set<T>()
            .Where(expression);
    }
}
