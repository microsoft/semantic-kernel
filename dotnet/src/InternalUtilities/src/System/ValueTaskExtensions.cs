// Copyright (c) Microsoft. All rights reserved.

#if !NETCOREAPP

using System;
using System.Threading.Tasks;

/// <summary>
/// Convenience extensions for ValueTask patterns within .netstandard2.0 projects.
/// </summary>
internal static class ValueTaskExtensions
{
    /// <summary>
    /// Creates a <see cref="ValueTask{TResult}"/> that's completed successfully with the specified result.
    /// </summary>
    /// <example>
    /// <c>
    /// int value = 33;
    /// return value.AsValueTask();
    /// </c>
    /// </example>
    public static ValueTask<TValue> AsValueTask<TValue>(this TValue value) => new(value);

    /// <summary>
    /// Creates a <see cref="ValueTask{TResult}"/> that's failed and is associated with an exception.
    /// </summary>
    /// <example>
    /// <c>
    /// int value = 33;
    /// return value.AsValueTask();
    /// </c>
    /// </example>
    public static ValueTask<TValue> AsValueTask<TValue>(this Exception exception) => new(Task.FromException<TValue>(exception));

    /// <summary>
    /// Present a regular task as a ValueTask.
    /// </summary>
    /// <example>
    /// <c>return Task.CompletedTask.AsValueTask();</c>
    /// </example>
    public static ValueTask AsValueTask(this Task task) => new(task);
}

#endif
