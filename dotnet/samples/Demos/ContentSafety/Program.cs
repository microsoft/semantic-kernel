// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.AI.ContentSafety;
using ContentSafety.Extensions;
using ContentSafety.Filters;
using ContentSafety.Handlers;
using ContentSafety.Options;
using ContentSafety.Services.PromptShield;
using Microsoft.SemanticKernel;

var builder = WebApplication.CreateBuilder(args);

// Get configuration
var config = new ConfigurationBuilder()
    .SetBasePath(Directory.GetCurrentDirectory())
    .AddJsonFile("appsettings.json")
    .AddJsonFile("appsettings.Development.json", true)
    .AddUserSecrets<Program>()
    .Build();

var openAIOptions = config.GetValid<OpenAIOptions>(OpenAIOptions.SectionName);
var azureContentSafetyOptions = config.GetValid<AzureContentSafetyOptions>(AzureContentSafetyOptions.SectionName);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole());

// Add Semantic Kernel
builder.Services.AddKernel();
builder.Services.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);

// Add Semantic Kernel prompt content safety filters
builder.Services.AddSingleton<IPromptRenderFilter, TextModerationFilter>();
builder.Services.AddSingleton<IPromptRenderFilter, AttackDetectionFilter>();

// Add Azure AI Content Safety services
builder.Services.AddSingleton<ContentSafetyClient>(_ =>
{
    return new ContentSafetyClient(
        new Uri(azureContentSafetyOptions.Endpoint),
        new AzureKeyCredential(azureContentSafetyOptions.ApiKey));
});

builder.Services.AddSingleton<PromptShieldService>(serviceProvider =>
{
    return new PromptShieldService(
        serviceProvider.GetRequiredService<ContentSafetyClient>(),
        azureContentSafetyOptions);
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
