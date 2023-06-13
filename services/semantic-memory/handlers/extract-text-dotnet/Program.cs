// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Services.Configuration;
using Microsoft.SemanticKernel.TextExtractionHandler;

IHost app = HostedHandlerBuilder.Build<TextExtractionHandler>();

app.Run();
