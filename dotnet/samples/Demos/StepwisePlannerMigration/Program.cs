// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using StepwisePlannerMigration.Extensions;
using StepwisePlannerMigration.Options;
using StepwisePlannerMigration.Services;

var builder = WebApplication.CreateBuilder(args);

// Get configuration
var config = new ConfigurationBuilder()
    .SetBasePath(Directory.GetCurrentDirectory())
    .AddJsonFile("appsettings.json")
    .AddJsonFile("appsettings.Development.json", true)
    .AddUserSecrets<Program>()
    .Build();

var openAIOptions = config.GetValid<OpenAIOptions>(OpenAIOptions.SectionName);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole());
builder.Services.AddTransient<IPlanProvider, PlanProvider>();

// Add Semantic Kernel
builder.Services.AddKernel();
builder.Services.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);

//builder.Services.AddTransient<FunctionCallingStepwisePlanner>();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseAuthorization();

app.MapControllers();

app.Run();
