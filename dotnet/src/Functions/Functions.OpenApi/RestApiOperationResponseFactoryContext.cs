// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the context for the <see cref="RestApiOperationResponseFactory"/>."/>
/// </summary>
public sealed class RestApiOperationResponseFactoryContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponseFactoryContext"/> class.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="response">The HTTP response message.</param>
    /// <param name="internalFactory">The internal factory to create instances of the <see cref="RestApiOperationResponse"/>.</param>
    internal RestApiOperationResponseFactoryContext(RestApiOperation operation, HttpRequestMessage request, HttpResponseMessage response, RestApiOperationResponseFactory internalFactory)
    {
        this.InternalFactory = internalFactory;
        this.Operation = operation;
        this.Request = request;
        this.Response = response;
    }

    /// <summary>
    /// The REST API operation.
    /// </summary>
    public RestApiOperation Operation { get; }

    /// <summary>
    /// The HTTP request message.
    /// </summary>
    public HttpRequestMessage Request { get; }

    /// <summary>
    /// The HTTP response message.
    /// </summary>
    public HttpResponseMessage Response { get; }

    /// <summary>
    /// The internal factory to create instances of the <see cref="RestApiOperationResponse"/>.
    /// </summary>
    public RestApiOperationResponseFactory InternalFactory { get; }
}
