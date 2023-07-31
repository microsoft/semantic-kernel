// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Azure.Functions.Worker.Http;

namespace Extensions;
public interface IAIPluginRunner
{
    public Task<HttpResponseData> RunAIPluginOperationAsync(HttpRequestData req, string operationId);
}
