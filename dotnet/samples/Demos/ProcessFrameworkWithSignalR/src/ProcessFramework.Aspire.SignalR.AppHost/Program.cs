// Copyright (c) Microsoft. All rights reserved.

using CommunityToolkit.Aspire.Hosting.Dapr;

var builder = DistributedApplication.CreateBuilder(args);

var openai = builder.AddConnectionString("openAiConnectionName");

var processOrchestrator = builder.AddProject<Projects.ProcessFramework_Aspire_SignalR_ProcessOrchestrator>("processorchestrator")
    .WithReference(openai)
    .WithDaprSidecar(new DaprSidecarOptions
    {
        AppPort = 7207,
        AppProtocol = "https"
    });

// var frontend = builder.AddProject<Projects.ProcessFramework_Aspire_SignalR_Frontend>("frontend")
//     .WithReference(processOrchestrator);

var frontend = builder.AddNpmApp("frontend", "../ProcessFramework.Aspire.SignalR.ReactFrontend", "dev")
    .WithReference(processOrchestrator);

builder.Build().Run();
