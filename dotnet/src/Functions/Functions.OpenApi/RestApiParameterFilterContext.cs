// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Initializes a new instance of the <see cref="RestApiParameterFilterContext"/> class.
/// </summary>
public sealed class RestApiParameterFilterContext
{
    /// <summary>
    /// The instance of <see cref="RestApiOperation"/> this parameter belongs to.
    /// </summary>
    public RestApiOperation Operation { get; set; }

    /// <summary>
    /// The instance of <see cref="RestApiParameter"/> to filter.
    /// </summary>
    public RestApiParameter Parameter { get; set; }

    /// <summary>
    /// The parent object of the parameter, can be either an instance
    /// of <see cref="RestApiPayload"/> or <see cref="RestApiPayloadProperty"/>
    /// null if the parameter belongs to the operation.
    /// </summary>
    public object? Parent { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="RestApiParameterFilterContext"/> class.
    /// </summary>
    /// <param name="operation">The REST API operation</param>
    /// <param name="parameter">The REST API parameter to filter.</param>
    internal RestApiParameterFilterContext(RestApiOperation operation, RestApiParameter parameter)
    {
        this.Operation = operation;
        this.Parameter = parameter;
    }
}
