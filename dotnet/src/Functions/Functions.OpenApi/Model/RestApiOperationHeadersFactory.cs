// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for creating headers for a REST API operation.
/// </summary>
/// <param name="operation">The REST API operation.</param>
/// <param name="arguments">The arguments for the operation.</param>
/// <param name="options">The operation run options.</param>
/// <returns>The operation headers.</returns>
internal delegate IDictionary<string, string>? RestApiOperationHeadersFactory(RestApiOperation operation, IDictionary<string, object?> arguments, RestApiOperationRunOptions? options);
