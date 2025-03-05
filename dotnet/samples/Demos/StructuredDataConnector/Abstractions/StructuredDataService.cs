// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using System.Linq.Expressions;

namespace StructuredDataConnector.Abstractions;

/// <summary>
/// Represents a connection to a data source.
/// </summary>
public class StructuredDataService : IDisposable
{
    /// <summary>
    /// Gets the database context.
    /// </summary>
    public DbContext Context { get; }

    /// <summary>
    /// Gets the list of allowed tables.
    /// </summary>
    public List<string> AllowedTables { get; set; } = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="StructuredDataService"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    public StructuredDataService(string connectionString)
    {
        this.Context = new DbContext(connectionString);
        this._internalContext = true;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StructuredDataService"/> class.
    /// </summary>
    /// <param name="dbContext">The database context.</param>
    public StructuredDataService(DbContext dbContext)
    {
        this.Context = dbContext;
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

    /// <summary>
    /// Searches for entities that match the specified expression.
    /// </summary>
    /// <param name="tableName">Table name to search.</param>
    /// <returns>A sequence of <see cref="Dictionary{TKey, TValue}"/> objects representing the search results.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the table is not allowed.</exception>
    public virtual async IAsyncEnumerable<Dictionary<string, object>> SearchByTableAsync(string tableName)
    {
        this.EnsureTableIsAllowed(tableName);

        this.Context.Database.Connection.Open();
        using (var command = this.Context.Database.Connection.CreateCommand())
        {
#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
            var sql = $"SELECT * FROM {tableName}";
            command.CommandText = sql;
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities

            using (var reader = await command.ExecuteReaderAsync().ConfigureAwait(false))
            {
                while (reader.Read())
                {
                    var record = new Dictionary<string, object>();
                    for (int i = 0; i < reader.FieldCount; i++)
                    {
                        record[reader.GetName(i)] = reader.GetValue(i);
                    }

                    yield return record;
                }
            }
        }
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

    private void EnsureTableIsAllowed(string tableName)
    {
        if (!this.AllowedTables.Contains(tableName))
        {
            throw new InvalidOperationException($"Table '{tableName}' is not allowed.");
        }
    }

    /*// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<KernelSearchResults<object>> GetSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    */

    private readonly bool _internalContext;
}
