// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.TestsShared.Services.Storage;

var builder = WebApplication.CreateBuilder(args);

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();

builder.Services.AddControllers();

// Registering storage used for persisting process state with Local Runtime
string tempDirectoryPath = Path.Combine(Path.GetTempPath(), "ProcessWithLocalRuntimeStorage");
var storageInstance = new JsonFileStorage(tempDirectoryPath);

builder.Services.AddSingleton<IProcessStorageConnector>(storageInstance);

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
app.Run();
