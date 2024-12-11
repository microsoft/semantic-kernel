// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

var builder = WebApplication.CreateBuilder(args);

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();

// Configure Dapr Actors
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});
// Configure Dapr Pubsub Client
//builder.Services.AddControllers().AddDapr();
builder.Services.AddDaprClient();

builder.Services.AddControllers();
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    // Configure the HTTP request pipeline.
    app.UseHttpsRedirection();
    app.UseAuthorization();
}

app.MapControllers();
app.MapActorsHandlers();
app.Run();
