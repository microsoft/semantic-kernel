// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate for filtering <see cref="RestApiParameter"/> instances.
/// </summary>
/// <remarks>
/// Implementations of this delegate can either return null which will cause the parameter
/// to be removed from the REST API or return a new instance of <see cref="RestApiParameter"/>
/// which will replace the original parameter.
/// </remarks>
/// <param name="context">Instance of <see cref="RestApiParameterFilterContext"/> containing details of the parameter to filter.</param>
public delegate RestApiParameter? RestApiParameterFilter(RestApiParameterFilterContext context);
