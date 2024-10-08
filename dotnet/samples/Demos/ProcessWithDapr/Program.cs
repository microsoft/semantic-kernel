// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

builder.Services.AddKernel();

builder.Services.AddHttpClient("SKClient", static (client) =>
{
    client.Timeout = TimeSpan.FromMinutes(5);
})
.ConfigurePrimaryHttpMessageHandler(static () =>
{
    var handler = new HttpClientHandler();
    handler.CheckCertificateRevocationList = false;
    return handler;
});

builder.Services.AddActors(static options =>
{
    // Register actor types and configure actor settings
    options.AddProcessActors();
});

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
