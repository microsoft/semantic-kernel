// Copyright (c) Microsoft. All rights reserved.

var builder = DistributedApplication.CreateBuilder(args);

// Deploy and provision Azure OpenAI service with AI models
var azureOpenAI = AddAzureOpenAIDeployments(builder);

// Deploy and provision Api Service
var apiService = builder.AddProject<Projects.ChatWithAgent_ApiService>("apiservice")
    .WithReference(azureOpenAI);

// Deploy and provision Web Frontend
builder.AddProject<Projects.ChatWithAgent_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();

static IResourceBuilder<IResourceWithConnectionString> AddAzureOpenAIDeployments(IDistributedApplicationBuilder appBuilder)
{
    if (appBuilder.ExecutionContext.IsPublishMode)
    {
        // Deploy and provision Azure OpenAI service with AI models
        return appBuilder.AddAzureOpenAI("azureOpenAI")
            .AddDeployment(new AzureOpenAIDeployment("chatModelDeployment", "gpt-4o-mini", "2024-07-18"))
            .AddDeployment(new AzureOpenAIDeployment("embeddingsModelDeployment", "text-embedding-ada-002", "2"));
    }

    // Use an existing Azure OpenAI service via connection string
    return appBuilder.AddConnectionString("azureOpenAI");
}
