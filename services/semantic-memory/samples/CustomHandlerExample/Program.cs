// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Services.Configuration;

var builder = HostedHandlersBuilder.CreateApplicationBuilder();
builder.AddHandler<MyHandler>("mypipelinestep");
//builder.AddHandler<MyHandler2>();
//builder.AddHandler<MyHandler3>();
var app = builder.Build();

// Quicker way, if you have just one handler
// IHost app = HostedHandlersBuilder.Build<MyHandler>("...");

app.Run();
