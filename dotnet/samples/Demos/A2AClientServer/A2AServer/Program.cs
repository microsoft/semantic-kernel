// Copyright (c) Microsoft. All rights reserved.
using A2A;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using SharpA2A.AspNetCore;
using SharpA2A.Core;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient().AddLogging();
var app = builder.Build();

var configuration = app.Configuration;
var httpClient = app.Services.GetRequiredService<IHttpClientFactory>().CreateClient();
var logger = app.Logger;

string apiKey = configuration["OPENAI_API_KEY"] ?? throw new ArgumentException("OPENAI_API_KEY must be provided");
string modelId = configuration["OPENAI_CHAT_MODEL_ID"] ?? "gpt-4.1";
string baseAddress = configuration["AGENT_URL"] ?? "http://localhost:5000";

var invoiceAgent = new InvoiceAgent(modelId, apiKey, logger);
var invoiceTaskManager = new TaskManager();
invoiceAgent.Attach(invoiceTaskManager);
app.MapA2A(invoiceTaskManager, "/invoice");

var currencyAgent = new CurrencyAgent(modelId, apiKey, logger);
var currencyTaskManager = new TaskManager();
currencyAgent.Attach(currencyTaskManager);
app.MapA2A(currencyTaskManager, "/currency");

await app.RunAsync();
