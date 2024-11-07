﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using SemanticKernel.Process.IntegrationTests;

var builder = WebApplication.CreateBuilder(args);

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();

// Configure Dapr
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
    options.Actors.RegisterActor<HealthActor>();
});

builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.TypeInfoResolver = new ProcessStateTypeResolver<KickoffStep>();
});

var app = builder.Build();

app.MapControllers();
app.MapActorsHandlers();
app.Run();
