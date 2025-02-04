// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for reading HTTP response content.
/// </summary>
/// <param name="context">The context containing HTTP operation details.</param>
/// <param name="cancellationToken">The cancellation token.</param>
/// <returns>The HTTP response content.</returns>
public delegate Task<object?> HttpResponseContentReader(HttpResponseContentReaderContext context, CancellationToken cancellationToken = default);
