---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-11-8
contact: alliscode
deciders: markwallace, mabolan
consulted: SergeyMenshykh
informed:
---

# Providing more type information to SKFunctions and Planners

## Context and Problem Statement

Today, Semantic Kernel only retains a small amount of information about the parameters of SKFunctions, and no information at all about the output of an SKFunction. This has a large negative impact on the effectiveness of our planners because it is not possible to adequately describe the schema of the the plugin function's inputs and outputs.

Planners depend on a description of the plugins available to it, which we refer to as a Functions Manual. Think of this as the user manual that is provided to the LLM and is intended to explain to the LLM the functions that are available to it and how they can be used. An example of a current Functions Manual from our Sequential planner looks like this:

```
DatePluginSimpleComplex.GetDate1:
  description: Gets the date with the current date offset by the specified number of days.
  inputs:
    - numDays: The number of days to offset the date by from today. Positive for future, negative for past.

WeatherPluginSimpleComplex.GetWeatherForecast1:
  description: Gets the weather forecast for the specified date and the current location, and time.
  inputs:
    - date: The date for the forecast
```

This Functions Manual describes two plugin functions that are available to the LLM, one to get the current date with an offset in days, and one to get the weather forecast for a given date. A simple question that our customer might want our planners to be able to answer with these plugin functions would be "What is the weather forecast for tomorrow?". Creating and executing a plan to answer this question would require invoking the first function, and then passing the result of that as a parameter to the invocation of the second function. If written in pseudo code, the plan would look something like this:

```csharp
var dateResponse = DatePluginSimpleComplex.GetDate1(1);
var forecastResponse = WeatherPluginSimpleComplex.GetWeatherForecast1(dateResponse);
return forecastResponse;
```

This seems like a reasonable plan, and this is indeed comparable to what out Sequential planner would come up with. This might also work, as long as the unknown return type of the first function happens to match the unknown parameter type of the second function. The Functions Manual that we are providing to the LLM however, does not specify the necessary information to know if these types will match up.

One way that we could provide the missing type information is to use Json Schema. This also happens to be the same way that OpenAPI specs provide type information for inputs and outputs, and this provides a cohesive solution for local and remote plugins. If we utilize Json Schema, then our Functions Manual can look more like this:

```json
[
  {
    "name": "DatePluginSimpleComplex.GetDate1",
    "description": "Gets the date with the current date offset by the specified number of days.",
    "parameters": {
      "type": "object",
      "required": ["numDays"],
      "properties": {
        "numDays": {
          "type": "integer",
          "description": "The number of days to offset the date by from today. Positive for future, negative for past."
        }
      }
    },
    "responses": {
      "200": {
        "description": "Successful response.",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": { "date": { "type": "string" } },
              "description": "The date."
            }
          }
        }
      }
    }
  },
  {
    "name": "WeatherPluginSimpleComplex.GetWeatherForecast1",
    "description": "Gets the weather forecast for the specified date and the current location, and time.",
    "parameters": {
      "type": "object",
      "required": ["date"],
      "properties": {
        "date": { "type": "string", "description": "The date for the forecast" }
      }
    },
    "responses": {
      "200": {
        "description": "Successful response.",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": { "degreesFahrenheit": { "type": "integer" } },
              "description": "The forecasted temperature in Fahrenheit."
            }
          }
        }
      }
    }
  }
]
```

This Functions Manual provides much more information about the the inputs and outputs of the functions that the LLM has access to. It allows to see that the output of the first functions is a complex objects that contain the information required by the second function. This also comes with an increase in the amount of tokens used, however the increase in functionality derived the type information outweighs this expense. With this information we can now expect the LLM to generate a plan that includes an understanding of how values should be extracted from outputs and passed to inputs. One effective method that we've used in testing is to ask the LLM to specify inputs as a Json Path into the appropriate output. An equivalent plan shown in pseudo code would look like this:

```csharp
var dateResponse = DatePluginSimpleComplex.GetDate1(1);
var forecastResponse = WeatherPluginSimpleComplex.GetWeatherForecast1(dateResponse.date);
return forecastResponse.degreesFahrenheit;
```

## Proposal

In order to be able to generate complete Function Manuals such as the Json Schema based examples above, SKFunctions and their associated Function Views will need to maintain more information about their parameter types and return types. Function Views currently have the following definition:

```csharp
public sealed record FunctionView(
    string Name,
    string PluginName,
    string Description = "",
    IReadOnlyList<ParameterView>? Parameters = null)
{
    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();
}
```

The function parameters are described by the collection of `ParameterView` objects which contain a semantic description, and provide a place to add more type information. There is however no existing place to put the type information and semantic description of the function output. To fix this we will add a new property called `ReturnParameterView` to the `FunctionView`:

```csharp
public sealed record FunctionView(
    string Name,
    string PluginName,
    string Description = "",
    IReadOnlyList<ParameterView>? Parameters = null,
    ReturnParameterView? ReturnParameter = null)
{
    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();

    /// <summary>
    /// Function output
    /// </summary>
    public ReturnParameterView ReturnParameter { get; init; } = ReturnParameter ?? new ReturnParameterView();
}
```

`ParameterView` objects currently contain a `ParameterViewType` property which contains some information about the type of the parameter but is limited to JSON types ([string, number, boolean, null, object, array]) and has no way of describing the structure of an object. To add the extra type information that is needed, we can add a native `System.Type` property. This would work well for local functions as the parameter Type would always be accessible when importing the SKFunction. It will also be required for hydrating native types from LLM responses. For remote plugins however, the native type for objects will not be known and may not even exist so the `System.Type` doesn't help. For this case we need to extract the type information from the OpenAPI specification and store it in a property that allows for previously unknown schemas. Options for this property type include `JsonSchema` from an OSS library such as JsonSchema.Net or NJsonSchema, `JsonDocument` from System.Text.Json, or a `string` containing the Json serialized schema.

| Type                      | Pros                                                         | Cons                                                       |
| ------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- |
| JsonSchema.Net.JsonSchema | Popular and has frequent updates, built on top of System.Net | Takes a dependency on OSS in SK core                       |
| NJsonShema.JsonSchema     | Very popular, frequent updates, long term project            | Built on top of Json.Net (Newtonsoft)                      |
| JsonDocument              | Native C# type, fast and flexible                            | Not a Json Schema, but a Json DOM container for the schema |
| String                    | Native C# type                                               | Not a Json Schema or Json DOM, very poor type hinting      |

To avoid taking a dependency on 3rd party libraries in the core abstractions project, we will use a `JsonDocument` type to hold the Json Schemas that are created when loading remote plugins. The libraries needed to create or extract these schemas can be included in the packages that require them, namely Functions.OpenAPI, Planners.Core, and Connectors.AI.OpenAI. The `NativeType` property will be populated when loading native functions and will be used to generate a Json Schema when needed, as well as for hydrating native types from LLM responses in planners and semantic functions.

```csharp
public sealed record ParameterView(
    string Name,
    string? Description = null,
    string? DefaultValue = null,
    ParameterViewType? Type = null,
    bool? IsRequired = null,
    Type? NativeType = null,
    JsonDocument? Schema = null);
```
