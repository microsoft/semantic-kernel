// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a factory for creating instances of the <see cref="RestApiOperationResponse"/>.
/// </summary>
/// <param name="context">The context that contains the operation details.</param>
/// <param name="cancellationToken">The cancellation token used to signal cancellation.</param>
/// <returns>A task that represents the asynchronous operation, containing an instance of <see cref="RestApiOperationResponse"/>.</returns>
public delegate Task<RestApiOperationResponse> RestApiOperationResponseFactory(RestApiOperationResponseFactoryContext context, CancellationToken cancellationToken = default);
