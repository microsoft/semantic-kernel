using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

// Initialize logging
using ILoggerFactory loggerFactory = LoggingServices.CreateLoggerFactory();

// Read configuration settings
FoundrySettings settings = ConfigurationServices.GetFoundrySettings();

// Create the project client, with credential.  Note, can use `AzureCliCredential` with `az login`.
AIProjectClient projectClient = new(settings.ConnectionString, new DefaultAzureCredential());

// Create a new agent definition
AgentsClient agentsClient = projectClient.GetAgentsClient();
Agent definition =
    await agentsClient.CreateAgentAsync(
        settings.ChatDeploymentName,
        name: "OutdoorActivityPlanner",
        description: "Provides information about the current time, physical user location, and weather.",
        instructions:
            """
            You are an Outdoor Activity Planner:

            - **Primary Goal**
              - Help the user decide *when* to schedule or carry out an outdoor activity.  
              - Offer new suggestions or review the user’s proposed timing, taking into account temperature, precipitation, wind, UV index, daylight hours, etc.

            - **Tone & Manner**  
              - Concise initial response.
              - More detail when requested or useful
              - Stay focused on planning or reviewing outdoor activities.

            - **Behavior**  
              1. **Use tools** to access information about the world, including the users physical location.
              2. **Ask clarifying questions** only when required for information that is outside of your capabilities to determine.
              3. **Summarize** the weather outlook succinctly (“Tomorrow morning looks clear and cool; best for a run.”).  
              4. **Recommend specific windows** (“Between 4 PM and 6 PM on Thursday, UV levels drop and temperatures hit the low 70s.”).  
              5. **Warn** of any hazards or changing conditions (“Rain arrives after noon, so plan your hike earlier.”).  
              6. **Offer alternatives** if the weather or timing isn’t ideal (“If it’s still too hot, consider doing it at sunrise instead.”).

            Whenever the user asks about an outdoor plan, use your knowledge of time, location, and weather to give them a crisp, on-point answer.
            """,
        tools: [new CodeInterpreterToolDefinition()],
        toolResources: null);

try
{
    // Define kernel with logging services
    IKernelBuilder builder = Kernel.CreateBuilder();
    builder.Services.AddSingleton(loggerFactory);

    // Import plugin
    builder.Plugins.AddFromType<WorldPlugin>();

    // Build kernel
    Kernel kernel = builder.Build();

    // Create agent
    AzureAIAgent agent =
        new(definition, agentsClient)
        {
            Kernel = kernel,
        };

    // Start interactive chat
    await ChatConsole.ChatAsync(agent);
}
finally
{
    // Clean-up
    await agentsClient.DeleteAgentAsync(definition.Id);
}
