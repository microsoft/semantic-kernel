// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Functions.OpenAPI;

/// <summary>
/// Represents a delegate for serializing REST API operation response content.
/// </summary>
/// <param name="content">The operation response content.</param>
/// <returns>The serialized HTTP response content.</returns>
internal delegate Task<object> HttpResponseContentSerializer(HttpContent content);
