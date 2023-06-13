// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Services.Configuration;
using Microsoft.SemanticKernel.Services.Storage.ContentStorage;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;
using Microsoft.SemanticKernel.TextExtractionHandler;

IHost app = AppBuilder.Build();

// Azure Blobs or FileSystem, depending on settings in appsettings.json
var storage = app.Services.GetService<IContentStorage>();

// Data pipelines orchestrator
var orchestrator = new InProcessPipelineOrchestrator(storage!);

// Text extraction handler
var textExtraction = new TextExtractionHandler(orchestrator);
await orchestrator.AttachHandlerAsync("extract", textExtraction);

// orchestrator.AttachHandlerAsync("partition", ...);
// orchestrator.AttachHandlerAsync("index", ...);

// Create sample pipeline with 4 files
var pipeline = orchestrator
    .PrepareNewFileUploadPipeline("inProcessTest", "userId", new[] { "vault1" })
    .AddUploadFile("file1", "file1.txt", "file1.txt")
    .AddUploadFile("file2", "file2.txt", "file2.txt")
    .AddUploadFile("file3", "file3.docx", "file3.docx")
    .AddUploadFile("file4", "file4.pdf", "file4.pdf")
    .Then("extract")
    // .Then("partition")
    // .Then("index")
    .Build();

// Execute pipeline
await orchestrator.RunPipelineAsync(pipeline);

Console.WriteLine("== Done ==");
