// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

var openai = builder.AddConnectionString("openAiConnectionName");

var translatorAgent = builder.AddProject<Projects.RemoteChatCompletionAgentDemo_TranslatorAgent>("translatoragent")
    .WithReference(openai);

var summaryAgent = builder.AddProject<Projects.RemoteChatCompletionAgentDemo_SummaryAgent>("summaryagent")
    .WithReference(openai);

var remoteChatCompletionAgent = builder.AddProject<Projects.RemoteChatCompletionAgentDemo_GroupChat>("groupChat")
    .WithReference(openai)
    .WithReference(translatorAgent)
    .WithReference(summaryAgent)
    .WithHttpCommand("/remote-group-chat", "Invoke Chat",
        commandOptions: new()
        {
            Method = HttpMethod.Get
        }
    );

builder.Build().Run();
