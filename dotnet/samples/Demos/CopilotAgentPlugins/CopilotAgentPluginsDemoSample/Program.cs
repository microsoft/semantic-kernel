// Copyright (c) Microsoft. All rights reserved.

using Spectre.Console.Cli;

var app = new CommandApp();
app.Configure(config =>
{
    config.AddCommand<DemoCommand>("demo");
});

return app.Run(args);
