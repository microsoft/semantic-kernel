# Process Framework with .NET Aspire

This demo aims to showcase how the [Semantic Kernel Process Framework](https://learn.microsoft.com/en-us/semantic-kernel/overview/) can be used with [.NET Aspire](https://learn.microsoft.com/en-us/dotnet/aspire/get-started/aspire-overview). The Process Framework allows developers to create business processes based on events. Each step of the process can be an agent or native code.

In this demo, I have defined the agents as external services, and each step will call these agents using HTTP requests. This setup allows .NET Aspire to add value by tracing the process using OpenTelemetry. Additionally, since each agent is a service, they can be restarted as needed using the .NET Aspire developer dashboard.

## Architecture

The business logic of this sample is pretty simple: we want to define a process that will translate some text in English and will then summarize it.

![Architecture Diagram](./docs/architecture.png)

## What is .NET Aspire?

.NET Aspire is a set of tools, templates, and packages for building observable, production ready apps. .NET Aspire is delivered through a collection of NuGet packages that bootstrap or improve specific challenges with modern app development.
.NET Aspire allows you to replace or extend parts with your preferred tools and workflows. Key features include:

- Dev-Time Orchestration: .NET Aspire provides features for running and connecting multi-project applications, container resources, and other dependencies for local development environments.
- Integrations: .NET Aspire integrations are NuGet packages for commonly used services, such as Redis or Postgres, with standardized interfaces ensuring they connect consistently and seamlessly with your app.
- Tooling: .NET Aspire comes with project templates and tooling experiences for Visual Studio, Visual Studio Code, and the .NET CLI to help you create and interact with .NET Aspire projects.

.NET Aspire orchestration assists with the following concerns:

- App composition: Specify the .NET projects, containers, executables, and cloud resources that make up the application.
- Service discovery and connection string management: The app host injects the right connection strings, network configurations, and service discovery information to simplify the developer experience.

### Running with .NET Aspire

To run this sample with .NET Aspire, simply clone the repository and run the following command:

```bash
cd scr/ProcessFramework.Aspire/ProcessFramework.Aspire.AppHost
dotnet run
```

We will see in the browser a dashboard that looks like this:
![Aspire Dashboard](./docs/aspire-dashboard.png)

By invoking the `ProcessOrchestrator` service, we can start the process. I've provided a [http file](ProcessFramework.Aspire.ProcessOrchestrator\ProcessFramework.Aspire.ProcessOrchestrator.http) with a predefined request to start the process.

This will generate a trace in the Aspire dashboard that looks like this:
![Aspire Trace](./docs/aspire-traces.png)

And we can also monitor the metrics of each agents in the Metrics tab:
![Aspire Metrics](./docs/aspire-metrics.png)