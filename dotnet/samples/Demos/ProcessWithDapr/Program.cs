// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithDapr.Extensions;
using ProcessWithDapr.Hubs;
using ProcessWithDapr.Options;

var builder = WebApplication.CreateBuilder(args);

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

var openAIOptions = config.GetValid<OpenAIOptions>(OpenAIOptions.SectionName);

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();
builder.Services.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);

// Configure Dapr
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});

builder.Services.AddSingleton<ChatHub>();

// Configure SignalR
builder.Services.AddSignalR();
builder.Services.AddCors(options =>
{
    options.AddPolicy("CorsPolicy", builder => builder
    .AllowAnyMethod()
    .AllowAnyHeader()
    .AllowCredentials()
    .WithOrigins("http://localhost:5173"));
});

builder.Services.AddControllers();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
    app.UseCors("CorsPolicy");
}
else
{
    // Configure the HTTP request pipeline.
    app.UseHttpsRedirection();
    app.UseAuthorization();
}

app.MapControllers();
app.MapHub<ChatHub>("/chatHub");
app.MapActorsHandlers();
app.Run();
