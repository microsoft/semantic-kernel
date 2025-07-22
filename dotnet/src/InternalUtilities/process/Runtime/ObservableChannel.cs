// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.Internal;

// Workaround to have access to all channel items since Channel only allows reading the latest item.
internal class ObservableChannel<T>
{
    private readonly Channel<T> _channel;
    private readonly ConcurrentQueue<T> _snapshot = new();

    public ObservableChannel(Channel<T> channel, IEnumerable<T>? initialState = null)
    {
        this._channel = channel ?? throw new ArgumentNullException(nameof(channel));
        if (initialState != null)
        {
            foreach (var item in initialState)
            {
                this._snapshot.Enqueue(item);
                this._channel.Writer.TryWrite(item);
            }
        }
    }

    /// <summary>
    /// Returns a collection of the items in the channel
    /// </summary>
    /// <returns>An array containing the items</returns>
    public List<T> GetChannelSnapshot()
    {
        return this._snapshot.ToList();
    }

    #region Read related methods

    /// <inheritdoc cref="ChannelReader{T}.TryRead(out T)" />
    public bool TryRead(out T? item)
    {
        bool successRead = this._channel.Reader.TryRead(out item);
        if (successRead)
        {
            this._snapshot.TryDequeue(out _);
        }

        return successRead;
    }

    /// <inheritdoc cref="ChannelReader{T}.TryPeek(out T)" />
    public bool TryPeak(out T? item)
    {
        bool peekSuccess = this._channel.Reader.TryPeek(out item);
        return peekSuccess;
    }

    public async ValueTask<bool> WaitToReadAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            return await this._channel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw;
        }
    }
    #endregion
    #region Write related methods
    /// <inheritdoc cref="ChannelWriter{T}.WriteAsync(T, CancellationToken)" />
    public async ValueTask WriteAsync(T item, CancellationToken cancellationToken = default)
    {
        try
        {
            await this._channel.Writer.WriteAsync(item, cancellationToken).ConfigureAwait(false);
            this._snapshot.Enqueue(item);
        }
        catch (Exception ex)
        {
            throw;
        }
    }

    /// <inheritdoc cref="ChannelWriter{T}.TryWrite(T)" />
    public bool TryWrite(T item)
    {
        bool successWrite = this._channel.Writer.TryWrite(item);
        if (successWrite)
        {
            this._snapshot.Enqueue(item);
        }

        return successWrite;
    }

    public void Complete()
    {
        this._channel.Writer.Complete();
    }
    #endregion
}
