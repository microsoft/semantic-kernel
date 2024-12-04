// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for filtering <see cref="RestApiParameter"/> instances.
/// </summary>
/// <param name="parameter">The REST API parameter to filter.</param>
/// <param name="operation">The REST API operation</param>
/// <param name="parent">The parent object of the parameter, can be either an instance of <see cref="RestApiPayload"/> or <see cref="RestApiPayloadProperty"/> or null if the parameter belongs to the operation.</param>
[Experimental("SKEXP0040")]
public delegate RestApiParameter? RestApiParameterFilter(RestApiParameter parameter, RestApiOperation operation, object? parent = null);
