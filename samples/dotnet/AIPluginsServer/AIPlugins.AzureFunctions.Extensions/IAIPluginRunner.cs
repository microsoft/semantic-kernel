// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace AIPlugins.AzureFunctions.Extensions;
public interface IAIPluginRunner
{
    public Task<HttpResponseData> RunAIPluginOperationAsync(HttpRequestData req, string operationId);
}
