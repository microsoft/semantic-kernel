// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Functions.OpenAPI;

/// <summary>
/// Represents a delegate for creating HTTP content for a REST API operation.
/// </summary>
/// <param name="payload">The operation payload metadata.</param>
/// <param name="arguments">The operation arguments.</param>
/// <returns>The HTTP content representing the operation payload.</returns>
internal delegate HttpContent HttpContentFactory(RestApiOperationPayload? payload, IDictionary<string, string> arguments);
