// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Represents a delegate that provides authentication callback based on plugin manifest auth config.
/// </summary>
/// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
public delegate AuthenticateRequestAsyncCallback AuthenticateCallbackProvider(OpenAIAuthenticationManifest? manifest = null);
