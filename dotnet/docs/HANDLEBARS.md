# Handlebars Prompt Template

In the context of building prompts for an LLM, Handlebars provides a structured and flexible way to create dynamic prompt templates that can incorporate variables, conditionals, and loops.

> To read more about the design of the Handlebars prompt template, see [0023-handlebars-template-engine.md](../../../../docs/decisions/0023-handlebars-template-engine.md).

## Usage

### 1. Creating the Handlebars Prompt Template Factory and template config from prompt

```cs
var options = new HandlebarsPlannerOptions();

var templateFactory = new HandlebarsPromptTemplateFactory(options);

var promptTemplateConfig = new PromptTemplateConfig()
{
    Template = "You are an AI assistant. My name is {{name}}. What is the origin of my name?",
    TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
    Name = "CustomPrompt",
};
```

### 2. Creating and executing a semantic function

Option 1: Using the factory directly

```cs
// Create the prompt template
var handlebarsTemplate = templateFactory.Create(promptTemplateConfig);

// Invoke the function by rendering the template
var arguments = new KernelArguments();
var result = await handlebarsTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(true);
```

Option 2: Using the Kernel's built-in `CreateFunctionFromPrompt` function.

```cs
// Create the function
var function = kernel.CreateFunctionFromPrompt(
    promptConfig: promptTemplateConfig,
    promptTemplateFactory: promptTemplateFactory
);

// Invoke the function
var arguments = new KernelArguments();
var result = await kernel.InvokeAsync(function, arguments);
Console.WriteLine(result.GetValue<string>());
```

## Helpers

To extend the functionality of Handlebars, users may call helpers from their prompt template. Helpers are functions that can be called within a Handlebars template to perform various tasks, such as managing variables, manipulating data, serializing output, or executing conditional logic.

Users have the option to use:

- Any of the built-in [Handlebars.Net helpers](https://github.com/Handlebars-Net/Handlebars.Net.Helpers),
- Any built-in [Kernel system helpers](#kernel-system-helpers),
- Any function registered in the Kernel,

or they may register their own custom helpers using the [RegisterCustomHelpers](#registering-custom-helpers) option.

By default, all system helpers and Kernel functions are registered as custom helpers to the Handlebars Prompt Template Factory. If users want to use any built-in helpers from the [Handlebars.Net library](https://github.com/Handlebars-Net/Handlebars.Net.Helpers), they must specify their target categories in `HandlebarsPromptTemplateOptions.Categories`. SK honors all options defined by [HandlebarsHelperOptions](https://github.com/Handlebars-Net/Handlebars.Net.Helpers/blob/8f7c9c082e18845f6a620bbe34bf4607dcba405b/src/Handlebars.Net.Helpers/Options/HandlebarsHelpersOptions.cs#L12).

### Handlebars.Net library helpers

```cs
public static readonly HandlebarsPromptTemplateOptions PromptTemplateOptions = new()
{
    // Options for built-in Handlebars helpers
    // All categories: https://github.com/Handlebars-Net/Handlebars.Net.Helpers
    Categories = [Category.DateTime],
};
```

### Kernel System Helpers

### set

Sets variables in the Handlebars context, allowing you to store and reference values throughout the template.

```handlebars
{{set "destination" "Vietnam"}}
{{set "duration" "3 weeks"}}

You're a seasoned travel expert. A client seeks your guidance for a memorable
trip. They desire a 3-week adventure at the end of the year. Their chosen
destination is
{{destination}}. Provide a detailed itinerary including must-visit attractions,
recommended accommodations, transportation options, and any special experiences
unique to
{{destination}}. Remember to craft a personalized experience tailored to their
preferences and interests, ensuring they have an unforgettable journey.
```

### concat

Concatenates its arguments into a single string

```handlebars
{{concat "Welcome" "to" "our" "website!"}}
```

### array

Converts arguments into an array.

```handlebars
{{set "cities" (array "Paris" "London" "New York")}}
```

> The value of "cities" is [ "Paris", "London", "New York" ], an array object.

### json

Serializes an object to JSON format.

```handlebars
{{set "cities" (json (array "Paris" "London" "New York"))}}
```

> The value of "cities" is "[ "Paris", "London", "New York" ]", a string object.

### raw

Outputs raw content without processing. It's useful for including HTML or other content that you don't want Handlebars to interpret.

```handlebars
{{raw}}<div>This content will not be processed by Handlebars</div>{{/raw}}
```

### range

Generates a range of numbers from the start to end values (inclusive).

```handlebars
{{set "numbers" (range 1 5)}}
```

### or

Performs a logical OR operation on its arguments.

```handlebars
{{or true false}}
```

### add

Adds numeric arguments.

```handlebars
{{add 5 10 16}}
```

### subtract

Subtracts its numeric arguments

```handlebars
{{subtract 20 5}}
```

### equals

Checks if its two arguments are equal.

```handlebars
{{equals "apple" "apple"}}
```

### #message

Block helper that renders a message with the specified role.

> Role must be supported by the [ChatHistory](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.chatcompletion.chathistory?view=semantic-kernel-dotnet) object.

```handlebars
{{#message role="system"}}
  You are an AI assistant.
{{/message}}
{{#message role="user"}}
  {{ask}}
{{/message}}
```

### Registering custom helpers

1. Define a function that will register your custom callbacks.

```cs
/// Define a new class, preferably an Extensions class, to store your custom callback.
internal sealed class HandlebarsPromptTemplateExtensions
{
    /// The callback must define three parameters:
    /// 1. A callback representing the `RegisterHelperSafe` method to register new helpers with built-in conflict handling.
    /// 2. A HandlebarsPromptTemplateOptions representing the configuration for helpers.
    public static void RegisterCustomCreatePlanHelpers(
        RegisterHelperCallback registerHelper,
        HandlebarsPromptTemplateOptions options,
        KernelArguments executionContext
    )
    {
        // You can register one or more custom helpers.
        registerHelper("toUpperCase", static (Context context, Arguments arguments) =>
        {
            var parameter = arguments[0].ToString();
            return parameter.ToUpper();
        });

        registerHelper("toLowerCase", static (Context context, Arguments arguments) =>
        {
            var parameter = arguments[0].ToString();
            return parameter.ToLower();
        });
    }
}
```

2. Pass in the function reference in your `HandlebarsPromptTemplateOptions`.

```cs
public static readonly HandlebarsPromptTemplateOptions PromptTemplateOptions = new()
    {
        // Custom helpers
        RegisterCustomHelpers = HandlebarsPromptTemplateExtensions.RegisterCustomCreatePlanHelpers,
    };
```

## Examples

### Templatized Prompt Template

```handlebars
{{set "name" "Alex"}}
{{set "role" "Project Manager"}}
{{set "project" "building a new mobile app"}}
{{set "deadline" "two months"}}

As a
{{role}}, your primary responsibility is to oversee the successful completion of
projects. You're currently leading a team tasked with
{{project}}. To ensure smooth progress, communicate clearly with team members,
manage resources efficiently, and mitigate risks effectively. What strategies
will you implement to ensure the project stays on track and meets its
objectives?

{{! These can be set explicitly in the template or passed as values using Kernel Arguments }}
{{set
  "reminder"
  (concat "Please ensure the project is completed within " deadline ".")
}}
{{set "cities" (array "San Francisco" "New York" "London")}}
{{set "cityJson" (json cities)}}

Don't forget:
{{reminder}}
Also, consider expanding the project's scope to include potential markets in
{{cityJson}}. Here are details about your team and their current
responsibilities.

{{! Display team members and their responsibilities }}
{{#each teamMembers}}
  -
  {{name}},
  {{responsibility}}
{{/each}}

Instructions: 1. Review the current project details and the responsibilities of
the
{{role}}. 2. Consider the reminder regarding the project deadline and the
suggestion to expand into potential markets. 3. Take note of the team members
and their respective responsibilities within the project. 4. Generate a response
outlining strategies to ensure the project's success, addressing communication,
resource management, risk mitigation, and any additional considerations.
```

### Leveraging Chat History

```handlebars
// Prompt.handlebars

{{set "topic" "Artificial Intelligence"}}
{{set "goal" "to explain the concept of artificial intelligence to a beginner"}}

{{#message role="user"}}
  What is
  {{topic}}?
{{/message}}

{{#message role="system"}}
  You are an AI assistant.
{{/message}}

{{#message role="user"}}
  I'm trying to understand
  {{topic}}. Can you explain it to me?
{{/message}}

{{#message role="system"}}
  Certainly!
  {{topic}}
  refers to the simulation of human intelligence processes by machines,
  especially computer systems. It encompasses learning, reasoning,
  problem-solving, perception, and language understanding.
{{/message}}

{{#message role="user"}}
  That's fascinating! Can you give me an example of
  {{topic}}
  in real life?
{{/message}}

{{#message role="system"}}
  Of course! One example of
  {{topic}}
  in real life is virtual personal assistants like Siri, Alexa, and Google
  Assistant. These assistants use AI algorithms to understand spoken language
  and perform tasks such as setting reminders, answering questions, and
  controlling smart home devices.
{{/message}}

{{#message role="user"}}
  Wow, that makes sense! Have there been any recent news articles about this?
{{/message}}
```

When using the `#message` helper, the prompt template must be rendered twice. First, to format the prompt template. Second, to execute the semantic function.

```cs
// Render the prompt
var promptTemplateConfig = new PromptTemplateConfig()
{
    Template = "{Read in Prompt.handlebars}",
    TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
    Name = "Custom Chat History Prompt",
};

var handlebarsTemplate = templateFactory.Create(promptTemplateConfig);
var prompt =  await handlebarsTemplate!.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(true);

// Format chat history
ChatHistory chatMessages = this.GetChatHistoryFromPrompt(prompt);

// Get the chat completion results
var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var result = await chatCompletionService.GetChatMessageContentAsync(chatMessages).ConfigureAwait(false);
```

Helper to extract chat history from prompt

```cs
private ChatHistory GetChatHistoryFromPrompt(string prompt)
{
    // Extract the chat history from the rendered prompt
    string pattern = @"<(user~|system~|assistant~)>(.*?)<\/\1>";
    MatchCollection matches = Regex.Matches(prompt, pattern, RegexOptions.Singleline);

    // Add the chat history to the chat
    var chatMessages = new ChatHistory();
    foreach (Match m in matches.Cast<Match>())
    {
        string role = m.Groups[1].Value;
        string message = m.Groups[2].Value;

        switch (role)
        {
            case "user~":
                chatMessages.AddUserMessage(message);
                break;
            case "system~":
                chatMessages.AddSystemMessage(message);
                break;
            case "assistant~":
                chatMessages.AddAssistantMessage(message);
                break;
        }
    }

    return chatMessages;
}
```
