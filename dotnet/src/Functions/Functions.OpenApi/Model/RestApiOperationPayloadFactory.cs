// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for creating a payload for a REST API operation.
/// </summary>
/// <param name="operation">The REST API operation.</param>
/// <param name="arguments">The arguments for the operation.</param>
/// <param name="enableDynamicPayload">
/// Determines whether the operation payload is constructed dynamically based on operation payload metadata.
/// If false, the operation payload must be provided via the 'payload' property.
/// </param>
/// <param name="enablePayloadNamespacing">
/// Determines whether payload parameters are resolved from the arguments by
/// full name (parameter name prefixed with the parent property name).
/// </param>
/// <param name="options">The operation run options.</param>
/// <returns>The operation payload.</returns>
internal delegate (object Payload, HttpContent Content)? RestApiOperationPayloadFactory(RestApiOperation operation, IDictionary<string, object?> arguments, bool enableDynamicPayload, bool enablePayloadNamespacing, RestApiOperationRunOptions? options);
