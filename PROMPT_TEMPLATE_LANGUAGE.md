# SK Prompt Template Syntax

The Semantic Kernel prompt template language is a simple and powerful way to
define and compose AI functions **using plain text**.
You can use it to create natural language prompts, generate responses, extract
information, **invoke other prompts** or perform any other task that can be
expressed with text.

The language supports three basic features that allow you to (**#1**) include
variables, (**#2**) call external functions, and (**#3**) pass parameters to functions.

You don't need to write any code or import any external libraries, just use the
curly braces `{{...}}` to embed expressions in your prompts.
Semantic Kernel will parse your template and execute the logic behind it.
This way, you can easily integrate AI into your apps with minimal effort and
maximum flexibility.

## Variables

To include a variable value in your text, use the `{{$variableName}}` syntax.
For example, if you have a variable called `name` that holds the user's name,
you can write:

    Hello {{$name}}, welcome to Semantic Kernel!

This will produce a greeting with the user's name.

## Function calls

To call an external function and embed the result in your text, use the
`{{namespace.functionName}}` syntax.
For example, if you have a function called `weather.getForecast` that returns
the weather forecast for a given location, you can write:

    The weather today is {{weather.getForecast}}.

This will produce a sentence with the weather forecast for the default location
stored in the `input` variable.
The `input` variable is set automatically by the kernel when invoking a function.
For instance, the code above is equivalent to:

    The weather today is {{weather.getForecast $input}}.

## Function parameters

To call an external function and pass a parameter to it, use the
`{namespace.functionName $varName}` syntax.
For example, if you want to pass a different input to the weather forecast
function, you can write:

    The weather today in {{$city}} is {weather.getForecast $city}.
    The weather today in {{$region}} is {weather.getForecast $region}.

This will produce two sentences with the weather forecast for two different
locations, using the city stored in the `city` variable and the region name
stored in the `region` variable.

## Design Principles

The template language uses of the `$` symbol on purpose, to clearly distinguish
between variables, which are retrieved from local temporary memory, and
functions that retrieve content executing some code.

Branching features such as "if", "for", and code blocks are not part of SK's
template language. This reflects SK's design principle of using natural language
as much as possible, with a clear separation from conventional programming code.

By using a simple language, the kernel can also avoid complex parsing and
external dependencies, resulting in a fast and memory efficient processing.

## Semantic function example

Here's a very simple example of a semantic function defined with a prompt
template, using the syntax described.

`== File: skprompt.txt ==`

```
My name: {{msgraph.GetMyName}}
My email: {{msgraph.GetMyEmailAddress}}
Recipient: {{$recipient}}
Email to reply to:
=========
{{$sourceEmail}}
=========
Generate a response to the email, to say: {{$input}}

Include the original email quoted after the response.
```

If we were to write that function in C#, it would look something like:

```csharp
async Task<string> GenResponseToEmailAsync(
    string whatToSay,
    string recipient,
    string sourceEmail)
{
    try {
        string name = await this._msgraph.GetMyName();
    } catch {
        ...
    }

    try {
        string email = await this._msgraph.GetMyEmailAddress();
    } catch {
        ...
    }

    try {
        // Use AI to generate an email using the 5 given variables
        // Take care of retry logic, tracking AI costs, etc.
        string response = await ...

        return response;
    } catch {
        ...
    }
}
```
