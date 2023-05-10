// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

public delegate Task AuthenticateRequestAsyncCallback(HttpRequestMessage request);
