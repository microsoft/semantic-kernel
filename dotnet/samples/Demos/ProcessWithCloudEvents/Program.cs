// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph;
using ProcessWithCloudEvents.Controllers;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<GraphServiceClient>(GraphServiceProvider.CreateGraphService());

// For demo purposes making the Counter a singleton so it is not instantiated on every new request
builder.Services.AddSingleton<CounterWithCloudStepsController>();
builder.Services.AddSingleton<CounterWithCloudSubscribersController>();

// Add services to the container.
builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
