using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

// Initialize logging
using ILoggerFactory loggerFactory = LoggingServices.CreateLoggerFactory();

// Read configuration settings
FoundrySettings settings = ConfigurationServices.GetFoundrySettings();

// Create the project client, with credential.  Note, can use `AzureCliCredential` with `az login`.
AIProjectClient projectClient = new(settings.ConnectionString, new DefaultAzureCredential());

// Query the connection to discover the endpoint and key.  (For Inference use `ConnectionType.AzureAIServices`)
ConnectionProperties aiConnection = await projectClient.GetConnectionAsync(ConnectionType.AzureOpenAI);

// Define kernel with openai service connector
IKernelBuilder builder =
    Kernel.CreateBuilder()
        .AddAzureOpenAIChatCompletion(settings.ChatDeploymentName, aiConnection.GetEndpoint(), aiConnection.GetApiKey()!);

// Add logging services
builder.Services.AddSingleton(loggerFactory);

// Import plugin
builder.Plugins.AddFromType<WorldPlugin>();

// Build kernel
Kernel kernel = builder.Build();

// Create agent
ChatCompletionAgent agent =
    new()
    {
        Name = "OutdoorActivityPlanner",
        Description = "Provides information about the current time, physical user location, and weather.",
        Instructions =
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
        Kernel = kernel,
        Arguments = new(
            new PromptExecutionSettings
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
            }),
    };

// Start interactive chat
await ChatConsole.ChatAsync(agent);
