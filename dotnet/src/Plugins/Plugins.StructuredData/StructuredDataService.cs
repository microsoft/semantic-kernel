// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Entity;
using System.Linq;
using System.Linq.Expressions;
using System.Threading;
using System.Threading.Tasks;

#pragma warning disable CA1308 // Normalize strings to uppercase

namespace Microsoft.SemanticKernel;

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
        Verify.NotNull(dbContext);

        this.Context = dbContext;
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
        Verify.NotNull(entity);

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
        Verify.NotNull(entity);

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
        Verify.NotNull(entity);

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
    protected virtual Expression<Func<TEntity, bool>> ParseQuery<TEntity>(string? filter)
    {
        if (string.IsNullOrWhiteSpace(filter))
        {
            return p => true;
        }

        var param = Expression.Parameter(typeof(TEntity), "p");
        var conditions = filter.Split([" and ", " or "], StringSplitOptions.None);
        var isOr = filter.Contains(" or ");

        var expressions = conditions.Select(condition => ParseCondition<TEntity>(condition.Trim(), param));
        var combined = CombineExpressions(expressions, isOr);

        return Expression.Lambda<Func<TEntity, bool>>(combined, param);
    }

    private static Expression ParseCondition<TEntity>(string condition, ParameterExpression param)
    {
        return condition switch
        {
            var c when c.Contains("contains(") => ParseStringMethod(c, "contains", param, CreateContainsExpression),
            var c when c.Contains("startswith(") => ParseStringMethod(c, "startswith", param, CreateStartsWithExpression),
            var c when c.Contains("endswith(") => ParseStringMethod(c, "endswith", param, CreateEndsWithExpression),
            _ => ParseComparisonCondition<TEntity>(condition, param)
        };
    }

    private static BinaryExpression ParseComparisonCondition<TEntity>(string condition, ParameterExpression param)
    {
        var tokens = condition.Split(' ');
        var property = tokens[0];
        var op = tokens[1].ToLowerInvariant();
        var value = tokens[2].Trim('\'');

        var member = Expression.Property(param, property);

        return value.Equals("null", StringComparison.OrdinalIgnoreCase)
            ? CreateNullComparison(member, op)
            : CreateValueComparison(member, op, value);
    }

    private static BinaryExpression CreateNullComparison(MemberExpression member, string op)
    {
        var nullConstant = Expression.Constant(null, member.Type);
        return op switch
        {
            "eq" => Expression.Equal(member, nullConstant),
            "ne" => Expression.NotEqual(member, nullConstant),
            _ => throw new NotSupportedException($"Operator '{op}' is not supported for null comparisons.")
        };
    }

    private static BinaryExpression CreateValueComparison(MemberExpression member, string op, string value)
    {
        var memberType = Nullable.GetUnderlyingType(member.Type) ?? member.Type;
        var convertedValue = ConvertValue(value, memberType);
        var constant = Expression.Constant(convertedValue, member.Type);

        return op switch
        {
            "gt" => Expression.GreaterThan(member, constant),
            "lt" => Expression.LessThan(member, constant),
            "eq" => Expression.Equal(member, constant),
            "ne" => Expression.NotEqual(member, constant),
            "ge" => Expression.GreaterThanOrEqual(member, constant),
            "le" => Expression.LessThanOrEqual(member, constant),
            _ => throw new NotSupportedException($"Operator '{op}' is not supported.")
        };
    }

    private static object ConvertValue(string value, Type targetType)
    {
        return targetType == typeof(DateTime)
            ? DateTime.Parse(value)
            : Convert.ChangeType(value, targetType);
    }

    private static Expression ParseStringMethod(
        string condition,
        string methodName,
        ParameterExpression param,
        Func<Expression, Expression, Expression> createExpression)
    {
        var (property, value) = ParseMethodArguments(condition, methodName);
        var member = Expression.Property(param, property);
        var constant = Expression.Constant(value);
        return createExpression(member, constant);
    }

    private static (string property, string value) ParseMethodArguments(string condition, string methodName)
    {
        var start = condition.IndexOf(methodName + "(", StringComparison.OrdinalIgnoreCase) + methodName.Length + 1;
        var end = condition.LastIndexOf(")", StringComparison.OrdinalIgnoreCase);
        var args = condition.Substring(start, end - start).Split(',');
        return (args[0].Trim(), args[1].Trim().Trim('\''));
    }

    private static Expression CreateContainsExpression(Expression member, Expression value)
        => Expression.Call(member, typeof(string).GetMethod("Contains", [typeof(string)])!, value);

    private static Expression CreateStartsWithExpression(Expression member, Expression value)
        => Expression.Call(member, typeof(string).GetMethod("StartsWith", [typeof(string)])!, value);

    private static Expression CreateEndsWithExpression(Expression member, Expression value)
        => Expression.Call(member, typeof(string).GetMethod("EndsWith", [typeof(string)])!, value);

    private static Expression CombineExpressions(IEnumerable<Expression> expressions, bool isOr)
    {
        return expressions.Aggregate((current, next) =>
            isOr ? Expression.OrElse(current, next) : Expression.AndAlso(current, next));
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
