// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public interface IChatThread
{
    /// <summary>
    /// $$$
    /// </summary>
    string Id { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task AddUserMessageAsync(string message, CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task AddMessageAsync(ModelMessage message, CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="messageId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<ModelMessage> RetrieveMessageAsync(string messageId, CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<IEnumerable<ModelMessage>> ListMessagesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="assistantId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task InvokeAsync(string assistantId, CancellationToken cancellationToken = default);
}
