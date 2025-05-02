// Define configuration with environment variables, user secrets, or `settings.development.json`

// Initialize logging
using ILoggerFactory loggerFactory = LoggingServices.CreateLoggerFactory();

// Read configuration settings
FoundrySettings settings = ConfigurationServices.GetFoundrySettings();

// STEP #1: Create the `Kernel` object, with:
// - AI services
// - LoggingFactory
// - Plugin (recommended: WorldPlugin)

// STEP #2: Create Agent, either:
// - ChatCompletionAgent (recommended)
// - AzureAIAgent (stretch goal)

// STEP #3: Invoke Agent
// - Solicit user input
// - Stream the agent response
// - Capture / re-use the agent thread

Console.WriteLine("\nHello, Agents!\n");
