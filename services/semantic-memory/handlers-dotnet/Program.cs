// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Services.Configuration;
using Microsoft.SemanticKernel.Services.SemanticMemory.Handlers;

var builder = HostedHandlersBuilder.CreateApplicationBuilder();

builder.AddHandler<TextExtractionHandler>("extract");
// builder.AddHandler<TextPartitioningHandler>("partition");
// builder.AddHandler<IndexingHandler>("index");

var app = builder.Build();

app.Run();
