// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

var openai = builder.AddConnectionString("openAiConnectionName");

var translateAgent = builder.AddProject<Projects.ProcessFramework_Aspire_TranslatorAgent>("translatoragent")
    .WithReference(openai);

var summaryAgent = builder.AddProject<Projects.ProcessFramework_Aspire_SummaryAgent>("summaryagent")
    .WithReference(openai);

var processOrchestrator = builder.AddProject<Projects.ProcessFramework_Aspire_ProcessOrchestrator>("processorchestrator")
    .WithReference(translateAgent)
    .WithReference(summaryAgent)
    .WithHttpCommand("/api/processdoc", "Trigger Process",
        commandOptions: new()
        {
            Method = HttpMethod.Get
        }
    );

builder.Build().Run();
