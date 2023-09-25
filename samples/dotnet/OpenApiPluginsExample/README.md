# Open API Plugins Example
The chat example below is meant to demonstrate the use of an OpenAPI-based plugin (e.g., GitHub), a planner (e.g., ActionPlanner)
and chat completions to create a conversational experience with additional information from a plugin when needed.

The specific GitHub OpenAPI used is a reduced definition supporting viewing of pull requests.

## Preparing your environment
Before you get started, make sure you have the following requirements in place:
- [.NET 6.0 SDK](https://dotnet.microsoft.com/download/dotnet/6.0)
- [Azure OpenAI](https://aka.ms/oai/access) resource or an account with [OpenAI](https://platform.openai.com).

## Running the sample
1. Clone the repository
2. Open the `./appsettings.json` and configure your AI service and GitHub credentials.
3. Run the sample
   - In Visual Studio 2019 or newer, right-click on the `OpenApiPluginsExample` project, select "Set as Startup Project", then press `F5` to run and debug the application
   - OR open a terminal window, change directory to the `OpenApiPluginsExample` project, then run `dotnet run`.

## Using the sample
The sample will provide a simple chat interface the large language model (e.g., gpt-3.5-turbo) and the planner will invoke the GitHub plugin when needed.

When asking for results from GitHub, try using bounded asks such as "List the three most recent open pull requests and include the name, number, and state for each."