// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.AI.ContentSafety;
using ContentSafety.Extensions;
using ContentSafety.Filters;
using ContentSafety.Handlers;
using ContentSafety.Options;
using Microsoft.SemanticKernel;

var builder = WebApplication.CreateBuilder(args);

// Get configuration
var config = new ConfigurationBuilder()
    .SetBasePath(Directory.GetCurrentDirectory())
    .AddJsonFile("appsettings.json")
    .AddJsonFile("appsettings.Development.json")
    .Build();

var azureOpenAIOptions = config.GetValid<AzureOpenAIOptions>(AzureOpenAIOptions.SectionName);
var azureContentSafetyOptions = config.GetValid<AzureContentSafetyOptions>(AzureContentSafetyOptions.SectionName);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole());

// Add Semantic Kernel
builder.Services.AddKernel();
builder.Services.AddAzureOpenAIChatCompletion(
    azureOpenAIOptions.DeploymentName,
    azureOpenAIOptions.Endpoint,
    azureOpenAIOptions.ApiKey);

// Add Semantic Kernel filters
builder.Services.AddSingleton<IPromptRenderFilter, TextModerationFilter>();

// Add Azure AI Content Safety
builder.Services.AddSingleton<ContentSafetyClient>((serviceProvider) =>
{
    return new ContentSafetyClient(
        new Uri(azureContentSafetyOptions.Endpoint),
        new AzureKeyCredential(azureContentSafetyOptions.ApiKey));
});

// Add exception handlers
builder.Services.AddExceptionHandler<ContentSafetyExceptionHandler>();
builder.Services.AddProblemDetails();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseAuthorization();
app.UseExceptionHandler();

app.MapControllers();

app.Run();
