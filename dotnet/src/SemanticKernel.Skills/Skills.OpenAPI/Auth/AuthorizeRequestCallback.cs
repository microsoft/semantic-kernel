// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Auth;

public delegate void AuthorizeRequestCallback(HttpRequestMessage requestMessage);
