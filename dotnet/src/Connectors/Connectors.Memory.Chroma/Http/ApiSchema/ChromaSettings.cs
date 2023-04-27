// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

public class ChromaSettings
{
    public string ServerHost { get; set; } = String.Empty;
    public int ServerHttpPort{get; set; }
    public bool ServerSslEnabled { get; set; }
    public int GrpcPort { get; set; }
       
}