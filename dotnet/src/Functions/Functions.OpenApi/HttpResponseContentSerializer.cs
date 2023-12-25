// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for serializing REST API operation response content.
/// </summary>
/// <param name="content">The operation response content.</param>
/// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
/// <returns>The serialized HTTP response content.</returns>
internal delegate Task<object> HttpResponseContentSerializer(HttpContent content, CancellationToken cancellationToken);
