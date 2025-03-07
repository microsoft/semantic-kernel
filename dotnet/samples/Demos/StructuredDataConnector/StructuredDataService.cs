// Copyright (c) Microsoft. All rights reserved.

using System.Data.Entity;
using System.Linq.Expressions;
using System.Reflection.Metadata;

namespace StructuredDataConnector;

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
        this.Context = dbContext
            ?? throw new ArgumentNullException(nameof(dbContext));
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
        var expression = this.ParseQuery<TEntity>(query);

        return this.Context.Set<TEntity>().Where(expression);
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
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

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
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

        var entry = this.Context.Entry(entity);
        if (entry.State == EntityState.Detached)
        {
            this.Context.Set<TEntity>().Attach(entity);
            entry.State = EntityState.Modified;
        }

        return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
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
        if (entity is null) { throw new ArgumentNullException(nameof(entity)); }

        var entry = this.Context.Entry(entity);
        if (entry.State == EntityState.Detached)
        {
            this.Context.Set<TEntity>().Attach(entity);
        }
        this.Context.Set<TEntity>().Remove(entity);

        return await this.Context.SaveChangesAsync(cancellationToken).ConfigureAwait(false);
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
    /// Parses a filter string into an expression.
    /// </summary>
    /// <remarks>
    /// The filter query parameter is a string where users can pass expressions like
    /// <code>price gt 100 and category eq 'electronics'</code>
    /// </remarks>
    /// <typeparam name="TEntity">Entity type.</typeparam>
    /// <param name="filter">Filter string.</param>
    /// <returns>Expression representing the filter.</returns>
    /// <exception cref="NotSupportedException">Operator not supported.</exception>
    protected virtual Expression<Func<TEntity, bool>> ParseQuery<TEntity>(string filter)
    {
        if (string.IsNullOrWhiteSpace(filter))
        {
            return p => true;
        }

        var param = Expression.Parameter(typeof(TEntity), "p");
        var conditions = filter.Split(new[] { " and ", " or " }, StringSplitOptions.None);
        Expression combined = null;
        bool isOr = filter.Contains(" or ");

        foreach (var condition in conditions)
        {
            var trimmed = condition.Trim();
            Expression? current = null;

            if (trimmed.Contains("contains("))
            {
                current = ParseMethod(trimmed, "contains", param, (m, v) => Expression.Call(m, typeof(string).GetMethod("Contains", new[] { typeof(string) }), v));
            }
            else if (trimmed.Contains("startswith("))
            {
                current = ParseMethod(trimmed, "startswith", param, (m, v) => Expression.Call(m, typeof(string).GetMethod("StartsWith", new[] { typeof(string) }), v));
            }
            else if (trimmed.Contains("endswith("))
            {
                current = ParseMethod(trimmed, "endswith", param, (m, v) => Expression.Call(m, typeof(string).GetMethod("EndsWith", new[] { typeof(string) }), v));
            }
            else
            {
                var tokens = trimmed.Split(' ');
                var property = tokens[0];
                var op = tokens[1];
                var value = tokens[2].Trim('\'');

                var member = Expression.Property(param, property);
                ConstantExpression? constant = null;
                if (member.Type == typeof(DateTime?) || member.Type == typeof(DateTime))
                {
                    constant = Expression.Constant(DateTime.Parse(value));
                }
                else
                {
                    constant = Expression.Constant(Convert.ChangeType(value, member.Type));
                }

                current = op switch
                {
                    "gt" => Expression.GreaterThan(member, constant),
                    "lt" => Expression.LessThan(member, constant),
                    "eq" => Expression.Equal(member, constant),
                    _ => throw new NotSupportedException($"Operator {op} not supported")
                };
            }
        }

        static Expression ParseMethod(string condition, string methodName, ParameterExpression param, Func<Expression, Expression, Expression> methodCall)
        {
            var start = condition.IndexOf(methodName + "(") + methodName.Length + 1;
            var end = condition.LastIndexOf(")");
            var args = condition.Substring(start, end - start).Split(',');
            var property = args[0].Trim();
            var value = args[1].Trim().Trim('\'');

            var member = Expression.Property(param, property);
            var constant = Expression.Constant(value);
            return methodCall(member, constant);
        }

        return Expression.Lambda<Func<TEntity, bool>>(combined, param);
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
