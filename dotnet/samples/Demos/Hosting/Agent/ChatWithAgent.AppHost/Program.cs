// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

var apiService = builder.AddProject<Projects.ChatWithAgent_ApiService>("apiservice");

builder.AddProject<Projects.ChatWithAgent_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();
