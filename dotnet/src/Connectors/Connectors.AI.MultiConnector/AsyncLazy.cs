// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <inheritdoc />
internal sealed class AsyncLazy<T> : Lazy<Task<T>>
{
    public AsyncLazy(T value)
        : base(() => Task.FromResult(value))
    {
    }

    public AsyncLazy(Func<T> valueFactory, CancellationToken cancellationToken)
        : base(() => Task.Factory.StartNew<T>(valueFactory, cancellationToken, TaskCreationOptions.None, TaskScheduler.Current))
    {
    }

    public AsyncLazy(Func<Task<T>> taskFactory, CancellationToken cancellationToken)
        : base(() => Task.Factory.StartNew(taskFactory, cancellationToken, TaskCreationOptions.None, TaskScheduler.Current).Unwrap())
    {
    }
}
