---
status: proposed
contact: sergeymenshykh
date: 2024-10-25
deciders: dmytrostruk, markwallace, rbarreto, sergeymenshykh, westey-m, 
---

# Providing Payload for OpenAPI Functions

## Context and Problem Statement
Today, SK OpenAPI functions' payload can either be provided by a caller or constructed dynamically by SK from OpenAPI document metadata and provided arguments. 

This ADR provides an overview of the existing options that OpenAPI functionality currently has for handling payloads and proposes a new option to simplify dynamic creation of complex payloads.

## Overview of Existing Options for Handling Payloads in SK

### 1. The `payload` and the `content-type` Arguments
This option allows the caller to create payload that conforms to the OpenAPI schema and pass it as an argument to the OpenAPI function when invoking it.
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = false 
});

// Create the payload for the createEvent function
string payload = """
{
    "subject": "IT Meeting",
    "start": {
        "dateTime": "2023-10-01T10:00:00",
        "timeZone": "UTC"
    },
    "end": {
        "dateTime": "2023-10-01T11:00:00",
        "timeZone": "UTC"
    },
    "tags": [
        { "name": "IT" },
        { "name": "Meeting" }
    ]
}
""";

// Create arguments for the createEvent function
KernelArguments arguments = new ()
{
    ["payload"] = payload,
    ["content-type"] = "application/json"
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

Note that Semantic Kernel does not validate or modify the payload in any way. It is the caller's responsibility to ensure that the payload is valid and conforms to the OpenAPI schema.


### 2. Dynamic Payload Construction From Leaf Properties
This option allows SK to construct the payload dynamically based on the OpenAPI schema and the provided arguments. 
The caller does not need to provide the payload when invoking the OpenAPI function. However, the caller must provide the arguments 
that will be used as values for the payload properties of the same name.
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = true // It's true by default 
});

// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//     },
//    "duration": "PT1H",
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["dateTime"] = DateTimeOffset.Parse("2023-10-01T10:00:00"),
    ["timeZone"] = "UTC",
    ["duration"] = "PT1H",
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

This option traverses the payload schema starting from the root properties down and collects all leaf properties (properties that do not have any child properties) along the way. 
The caller must provide arguments for the identified leaf properties, and SK will construct the payload based on the schema and the provided arguments.

There is a limitation with this option regarding the creation of payloads that contain properties with the same names at different levels.
Taking into account that import process creates a kernel function for each OpenAPI operation, there's no feasible way to create a kernel function with more than one parameter having the same name.
An attempt to import a plugin with such a payload will fail with the following error: "The function has two or more parameters with the same name `<property-name>`."

Additionally, there's probability of circular references in the payload schema that may occur when two or more properties reference each other, creating a loop. 
SK will detect such circular references and throw an error failing the operation import.

Another specificity of this option is that it does not traverse array properties and considers them as leaf properties. 
This means that the caller must provide arguments for the properties of the array type, but not for the array elements or the properties of the array elements. 
In the example above, the array of objects should be provided as an argument for the "tags" array property.

### 3. Dynamic Payload Construction From Leaf Properties Using Namespaces
This option addresses the limitation of the dynamic payload construction option described above regarding handling properties with the same name at different levels.
It does so by prepending child property names with their parent property names, effectively creating unique names. 
The caller still needs to provide arguments for the properties and SK will do the rest.
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = true,
    EnablePayloadNamespacing = true
});


// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "end": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["start.dateTime"] = DateTimeOffset.Parse("2023-10-01T10:00:00"),
    ["start.timeZone"] = "UTC",
    ["end.dateTime"] = DateTimeOffset.Parse("2023-10-01T11:00:00"),
    ["end.timeZone"] = "UTC",
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

This option, like the previous one, traverses the payload schema from the root properties down to collect all leaf properties. When a leaf property is encountered, SK checks for a parent property. 
If a parent exists, the leaf property name is prepended with the parent property name, separated by a dot, to create a unique name.
For instance, the `dateTime` property of the `start` object will be named `start.dateTime`.  
   
This option treats array properties in the same way as the previous one, considering them as leaf properties, which means the caller must supply arguments for them.

This option is susceptible to circular references in the payload schema as well, and SK will fail the operation import if it detects any.

## New Options for Handling Payloads in SK

### Context and Problem Statement
SK goes above and beyond to handle the complexity of constructing payloads dynamically and offloading this responsibility from the caller.

However, neither of the existing options is suitable for complex scenarios when the payload contains properties with the same name at different levels and using namespaces is not an option.

To cover these scenarios, we propose a new option for handling payloads in SK.

### Considered Options

- Option #4: Construct payload out of root properties

### Option #4: Dynamic Payload Construction From Root Properties

There could be cases when the payload contains properties with the same name, and using namespaces is not possible for a various reasons. In order not to offload 
the responsibility of constructing the payload to the caller, SK can do an extra step and construct the payload out of the root properties. Of cause the complexity of building
arguments for those root properties will be on the caller side but there's not much SK can do if it's not allowed to use namespaces and arguments for properties with the same name at different levels
have to be resolved from the flat list of kernel arguments.

```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters { EnableDynamicPayload = false, EnablePayloadNamespacing = true });

// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "end": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["start"] = new MeetingTime() { DateTime = DateTimeOffset.Parse("2023-10-01T10:00:00"), TimeZone = TimeZoneInfo.Utc },
    ["end"] = new MeetingTime() { DateTime = DateTimeOffset.Parse("2023-10-01T10:00:00"), TimeZone = TimeZoneInfo.Utc },
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

This option naturally fits between existing option #1. The `payload` and the `content-type` Arguments and option #2. Dynamic Payload Construction Using Leaf Properties as shown in the overview table below.

### Options Overview
| Option | Caller | SK | Limitations |
|--------|-------|----|--------|
| 1. The `payload` and the `content-type` Arguments | Constructs payload | Use it as is | No limitations |
| 4. Dynamic Payload Construction From Root Properties | Provides arguments for root properties | Constructs payload | 1. No support for `anyOf`, `allOf`, `oneOf` |
| 2. Dynamic Payload Construction From Leaf Properties | Provides arguments for leaf properties | Constructs payload | 1. No support for `anyOf`, `allOf`, `oneOf`, 2. Leaf properties must be unique, 3. Circular references  |
| 3. Dynamic Payload Construction From Leaf Properties + Namespaces | Provides arguments for namespaced properties | Constructs payload | 1. No support for `anyOf`, `allOf`, `oneOf`, 2. Circular references |

### Decision Outcome
Having discussed these options, it was decided not to proceed with implementation of Option #4 because of absence of strong evidence that it provides any benefits over the existing Option #1.

## Samples
Samples demonstrating the usage of the existing options described above can be found in the [Semantic Kernel Samples repository](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_PayloadHandling.cs)