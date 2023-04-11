// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.Rest;

public delegate Task AuthenticateRequestAsyncCallback(HttpRequestMessage request);
