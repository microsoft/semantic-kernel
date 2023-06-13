// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Timers;
using Azure;
using Azure.Identity;
using Azure.Storage;
using Azure.Storage.Queues;
using Azure.Storage.Queues.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Timer = System.Timers.Timer;

namespace Microsoft.SemanticKernel.Services.Storage.Queue;

public sealed class AzureQueue : IQueue
{
    private sealed class MessageEventArgs : EventArgs
    {
        public QueueMessage? Message { get; set; }
    }

    private event AsyncMessageHandler<MessageEventArgs>? Received;

    /// <summary>
    /// Event triggered when a message is received
    /// </summary>
    // private event EventHandler<MessageEventArgs> Received;

    // How often to check if there are new messages
    private const int PollDelayMsecs = 100;

    // How many messages to fetch at a time
    private const int FetchBatchSize = 3;

    // How long to lock messages once fetched. Azure Queue default is 30 secs.
    private const int FetchLockSeconds = 300;

    // How many times to dequeue a messages and process before moving it to a poison queue
    private const int MaxRetryBeforePoisonQueue = 10;

    // Suffix used for the poison queues
    private const string PoisonQueueSuffix = "-poison";

    // Queue client builder, requiring the queue name in input
    private readonly Func<string, QueueClient> _clientBuilder;

    // Queue client, once connected
    private QueueClient? _queue;

    // Queue client, once connected
    private QueueClient? _poisonQueue;

    // Name of the queue
    private string _queueName = string.Empty;

    // Timer triggering the message dispatch
    private Timer? _dispatchTimer;

    // Application logger
    private readonly ILogger<AzureQueue> _log;

    // Lock helpers
    private readonly object _lock = new();
    private bool _busy = false;

    public AzureQueue(
        string connectionString,
        ILogger<AzureQueue>? logger = null)
        : this(GetClientBuilder(connectionString), logger)
    {
    }

    public AzureQueue(
        string accountName,
        string endpointSuffix = "core.windows.net",
        ILogger<AzureQueue>? logger = null)
        : this(GetClientBuilder(accountName, endpointSuffix), logger)
    {
    }

    public AzureQueue(
        string accountName,
        string accountKey,
        string endpointSuffix = "core.windows.net",
        ILogger<AzureQueue>? logger = null)
        : this(GetClientBuilder(accountName, accountKey, endpointSuffix), logger)
    {
    }

    public AzureQueue(Func<string, QueueClient> clientBuilder, ILogger<AzureQueue>? logger)
    {
        this._clientBuilder = clientBuilder;
        this._log = logger ?? NullLogger<AzureQueue>.Instance;
    }

    /// <inherit />
    public async Task<IQueue> ConnectToQueueAsync(string queueName, QueueOptions options = default, CancellationToken cancellationToken = default)
    {
        this._log.LogTrace("Connecting to queue name: {0}", queueName);

        if (string.IsNullOrEmpty(queueName))
        {
            this._log.LogError("The queue name is empty");
            throw new ArgumentOutOfRangeException(nameof(queueName), "The queue name is empty");
        }

        if (!string.IsNullOrEmpty(this._queueName))
        {
            this._log.LogError("The queue name has already been set");
            throw new InvalidOperationException($"The queue is already connected to `{this._queueName}`");
        }

        // Note: 3..63 chars, only lowercase letters, numbers and hyphens. No hyphens at start/end and no consecutive hyphens.
        this._queueName = queueName.ToLowerInvariant();
        this._log.LogDebug("Queue name: {0}", this._queueName);

        this._queue = this._clientBuilder(this._queueName);
        Response? result = await this._queue.CreateIfNotExistsAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        this._log.LogTrace("Queue ready: status code {0}", result?.Status);

        this._poisonQueue = this._clientBuilder(this._queueName + PoisonQueueSuffix);
        result = await this._poisonQueue.CreateIfNotExistsAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        this._log.LogTrace("Poison queue ready: status code {0}", result?.Status);

        if (options.DequeueEnabled)
        {
            this._log.LogTrace("Enabling dequeue on queue {0}, every {1} msecs", this._queueName, PollDelayMsecs);
            this._dispatchTimer = new Timer(TimeSpan.FromMilliseconds(PollDelayMsecs));
            this._dispatchTimer.Elapsed += this.DispatchMessages;
            this._dispatchTimer.Start();
        }

        return this;
    }

    /// <inherit />
    public async Task EnqueueAsync(string message, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(this._queueName) || this._queue == null)
        {
            this._log.LogError("The queue client is not connected, cannot enqueue messages");
            throw new InvalidOperationException("The client must be connected to a queue first");
        }

        this._log.LogDebug("Sending message...");
        Response<SendReceipt> receipt = await this._queue.SendMessageAsync(message, cancellationToken).ConfigureAwait(false);
        this._log.LogDebug("Message sent {0}", receipt.Value?.MessageId);
    }

    /// <inherit />
    public void OnDequeue(Func<string, Task<bool>> processMessageAction)
    {
        this.Received += async (object sender, MessageEventArgs args) =>
        {
            QueueMessage message = args.Message!;

            this._log.LogInformation("Message '{0}' received, expires at {1}", message.MessageId, message.ExpiresOn);

            try
            {
                if (message.DequeueCount <= MaxRetryBeforePoisonQueue)
                {
                    bool success = await processMessageAction.Invoke(message.MessageText).ConfigureAwait(false);
                    if (success)
                    {
                        this._log.LogDebug("Message '{0}' dispatch successful, deleting message", message.MessageId);
                        await this.DeleteMessageAsync(message).ConfigureAwait(false);
                    }
                    else
                    {
                        this._log.LogDebug("Message '{0}' dispatch rejected, putting message back in the queue with a delay", message.MessageId);
                        var backoffDelay = TimeSpan.FromSeconds(1 * message.DequeueCount);
                        await this.UnlockMessageAsync(message, backoffDelay).ConfigureAwait(false);
                    }
                }
                else
                {
                    this._log.LogError("Message '{0}' reached max attempts, moving to poison queue", message.MessageId);
                    await this.MoveMessageToPoisonQueueAsync(message).ConfigureAwait(false);
                }
            }
#pragma warning disable CA1031 // Must catch all to handle queue properly
            catch (Exception e)
            {
                // Note: exceptions in this block are caught by DispatchMessages()
                this._log.LogError(e, "Message '{0}' processing failed with exception, putting message back in the queue", message.MessageId);
                var backoffDelay = TimeSpan.FromSeconds(1 * message.DequeueCount);
                await this.UnlockMessageAsync(message, backoffDelay).ConfigureAwait(false);
            }
#pragma warning restore CA1031
        };
    }

    /// <inherit />
    public void Dispose()
    {
    }

    /// <summary>
    /// Create queue client using account name and Azure Identity credentials
    /// </summary>
    /// <param name="accountName">Account name (letters and digits only)</param>
    /// <param name="endpointSuffix">Azure suffix, usually "core.windows.net"</param>
    /// <returns>Function to invoke to create queue client</returns>
    public static Func<string, QueueClient> GetClientBuilder(string accountName, string endpointSuffix)
    {
        return queueName => new QueueClient(
            new($"https://{accountName}.queue.{endpointSuffix}/{queueName}"),
            new DefaultAzureCredential());
    }

    /// <summary>
    /// Create queue client using connection string
    /// </summary>
    /// <param name="connectionString">Connection string</param>
    /// <returns>Function to invoke to create queue client</returns>
    public static Func<string, QueueClient> GetClientBuilder(string connectionString)
    {
        return queueName => new QueueClient(connectionString, queueName);
    }

    /// <summary>
    /// Create queue client using account name and account key
    /// </summary>
    /// <param name="accountName">Account name (letters and digits only)</param>
    /// <param name="accountKey">Account key, primary or secondary</param>
    /// <param name="endpointSuffix">Azure suffix, usually "core.windows.net"</param>
    /// <returns>Function to invoke to create queue client</returns>
    public static Func<string, QueueClient> GetClientBuilder(string accountName, string accountKey, string endpointSuffix)
    {
        return queueName => new QueueClient(
            new($"https://{accountName}.queue.{endpointSuffix}/{queueName}"),
            new StorageSharedKeyCredential(accountName, accountKey));
    }

    /// <summary>
    /// Fetch messages from the queue and dispatch them
    /// </summary>
    private void DispatchMessages(object? sender, ElapsedEventArgs ev)
    {
        if (this._busy || this.Received == null || this._queue == null)
        {
            return;
        }

        lock (this._lock)
        {
            this._busy = true;

            QueueMessage[] messages = Array.Empty<QueueMessage>();

            // Fetch messages
            try
            {
                // Fetch and Hide N messages
                Response<QueueMessage[]> receiveMessages = this._queue.ReceiveMessages(FetchBatchSize, visibilityTimeout: TimeSpan.FromSeconds(FetchLockSeconds));
                if (receiveMessages.HasValue && receiveMessages.Value.Length > 0)
                {
                    messages = receiveMessages.Value;
                }
            }
            catch (Exception exception)
            {
                this._log.LogError(exception, "Fetch failed");
                this._busy = false;
                throw;
            }

            if (messages.Length == 0)
            {
                this._busy = false;
                return;
            }

            // Async messages dispatch
            this._log.LogTrace("Dispatching {0} messages", messages.Length);
            foreach (QueueMessage message in messages)
            {
                _ = Task.Factory.StartNew(async _ =>
                {
                    try
                    {
                        await this.Received(this, new MessageEventArgs { Message = message }).ConfigureAwait(false);
                    }
#pragma warning disable CA1031 // Must catch all to log and keep the process alive
                    catch (Exception e)
                    {
                        this._log.LogError(e, "Message '{0}' processing failed with exception", message.MessageId);
                    }
#pragma warning restore CA1031
                }, null);
            }

            this._busy = false;
        }
    }

    private Task DeleteMessageAsync(QueueMessage message)
    {
        return this._queue!.DeleteMessageAsync(message.MessageId, message.PopReceipt);
    }

    private Task UnlockMessageAsync(QueueMessage message, TimeSpan delay)
    {
        return this._queue!.UpdateMessageAsync(message.MessageId, message.PopReceipt, visibilityTimeout: delay);
    }

    private async Task MoveMessageToPoisonQueueAsync(QueueMessage message)
    {
        await this._poisonQueue!.CreateIfNotExistsAsync().ConfigureAwait(false);

        var poisonMsg = new
        {
            MessageText = message.MessageText,
            Id = message.MessageId,
            InsertedOn = message.InsertedOn,
            DequeueCount = message.DequeueCount,
        };

        var neverExpire = TimeSpan.FromSeconds(-1);
        await this._poisonQueue.SendMessageAsync(
            ToJson(poisonMsg),
            visibilityTimeout: TimeSpan.Zero,
            timeToLive: neverExpire).ConfigureAwait(false);
        await this.DeleteMessageAsync(message).ConfigureAwait(false);
    }

    private static string ToJson(object data, bool indented = false)
    {
        return JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = indented });
    }
}
