// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI;

/// <summary>
/// Represents a delegate for creating HTTP content for a REST API operation.
/// </summary>
/// <param name="payload">The operation payload metadata.</param>
/// <param name="arguments">The operation arguments.</param>
/// <returns>The HTTP content representing the operation payload.</returns>
public delegate HttpContent HttpContentFactory(RestApiOperationPayload? payload, IDictionary<string, string> arguments);
