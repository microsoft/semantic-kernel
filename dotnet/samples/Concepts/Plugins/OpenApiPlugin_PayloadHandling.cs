// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// These samples demonstrate how SK can handle payloads for OpenAPI functions. Today, SK can handle payloads in the following ways:
///   1. By accepting the payload from the caller. See the <see cref="InvokeOpenApiFunctionWithPayloadProvidedByCallerAsync"/> sample for more details.
///   2. By constructing the payload based on the function's schema from leaf properties. See the <see cref="InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesAsync"/> sample for more details.
///   3. By constructing the payload based on the function's schema from leaf properties with namespaces. See the <see cref="InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesWithNamespacesAsync"/> sample for more details.
///   4. [Proposed] By constructing the payload based on the function's schema from root properties. See the <see cref="InvokeOpenApiFunctionWithArgumentsForPayloadRootPropertiesAsync"/> sample for more details.
/// </summary>
public sealed class OpenApiPlugin_PayloadHandling : BaseTest
{
    private readonly Kernel _kernel;
    private readonly ITestOutputHelper _output;
    private readonly HttpClient _httpClient;

    public OpenApiPlugin_PayloadHandling(ITestOutputHelper output) : base(output)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            credentials: new AzureCliCredential());

        this._kernel = builder.Build();

        this._output = output;

        void RequestPayloadHandler(string requestPayload)
        {
            this._output.WriteLine("Request payload");
            this._output.WriteLine(requestPayload);
        }

        // Create HTTP client with a stub handler to log the request payload
        this._httpClient = new(new StubHttpHandler(RequestPayloadHandler));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with a payload provided by the caller.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithPayloadProvidedByCallerAsync()
    {
        // Create an Open API document for the Event Utils service
        using MemoryStream document = CreateOpenApiDocumentForEventUtilsService();

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", document, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = false // Disable dynamic payload construction
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "payload"
        //   Description: "REST API request body."
        //   ParameterType: "{Name = "Object" FullName = "System.Object"}"
        //   Schema: {
        //      "type": "object",
        //      "properties": {
        //          "subject": {
        //              "type": "string"
        //          },
        //          "start": {
        //              "required": ["dateTime", "timeZone"],
        //              "type": "object",
        //              "properties": {
        //                  "dateTime": {
        //                      "type": "string",
        //                      "description": "The start date and time of the meeting in ISO 8601 format.",
        //                      "format": "date-time"
        //                  },
        //                  "timeZone": {
        //                      "type": "string",
        //                      "description": "The time zone in which the meeting starts."
        //                  }
        //              }
        //          }
        //          "end": {
        //              "type": "object",
        //              "properties": Similar to the 'start' property one
        //          }
        //          "tags": {
        //              "type": "array",
        //              "items": {
        //                  "required": ["name"],
        //                  "type": "object",
        //                  "properties": {
        //                      "name": {
        //                          "type": "string",
        //                          "description": "A tag associated with the meeting for categorization."
        //                      }
        //                  }
        //              },
        //              "description": "A list of tags to help categorize the meeting."
        //          }
        //      }
        //   }
        // Parameter[1]
        //   Name: "content_type"
        //   Description: "Content type of REST API request body."
        //   ParameterType: { Name = "String" FullName = "System.String" }
        //   Schema: { "type": "string" }

        // Create the payload for the createEvent function.
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
        KernelArguments arguments = new()
        {
            ["payload"] = payload,
            ["content-type"] = "application/json"
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        AzureOpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload leaf properties.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesAsync()
    {
        // Create an Open API document for the simplified Event Utils service
        using MemoryStream document = CreateOpenApiDocumentForSimplifiedEventUtilsService();

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", document, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true // Enable dynamic payload construction. It is enabled by default.
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "subject"
        //   Description: "The subject or title of the meeting."
        //   ParameterType: { Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The subject or title of the meeting." }
        // Parameter[1]
        //   Name: "dateTime"
        //   Description: "The start date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The start date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[2]
        //   Name: "timeZone"
        //   Description: "The time zone in which the meeting is scheduled."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting is scheduled." }
        // Parameter[3]
        //   Name: "duration"
        //   Description: "Duration of the meeting in ISO 8601 format (e.g., 'PT1H' for 1 hour).."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "Duration of the meeting in ISO 8601 format (e.g., PT1H for 1 hour)." }
        // Parameter[4]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        //   Schema: { "type": "array", "items": { "required": ["name"], "type": "object", "properties": { "name": { "type": "string", "description": "A tag associated with the meeting for categorization." }}}, "description": "A list of tags to help categorize the meeting."}

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["subject"] = "IT Meeting",
            ["dateTime"] = "2023-10-01T10:00:00",
            ["timeZone"] = "UTC",
            ["duration"] = "PT1H",
            ["tags"] = """[ { "name": "IT" }, { "name": "Meeting" }  ]"""
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        AzureOpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload leaf properties with namespaces.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesWithNamespacesAsync()
    {
        // Create an Open API document for the Event Utils service
        using MemoryStream document = CreateOpenApiDocumentForEventUtilsService();

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", document, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true, // Enable dynamic payload construction. It is enabled by default.
            EnablePayloadNamespacing = true // Enable payload namespacing.
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "subject"
        //   Description: "The subject or title of the meeting."
        //   ParameterType: { Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The subject or title of the meeting." }
        // Parameter[1]
        //   Name: "start_dateTime"
        //   Description: "The start date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The start date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[2]
        //   Name: "start_timeZone"
        //   Description: "The time zone in which the meeting is scheduled."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting is scheduled." }
        // Parameter[3]
        //   Name: "end_dateTime"
        //   Description: "The end date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The end date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[4]
        //   Name: "end_timeZone"
        //   Description: "The time zone in which the meeting ends."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting ends." }
        // Parameter[5]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        // Parameter[3]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        //   Schema: {
        //      "type": "array",
        //      "items": {
        //          "required": ["name"],
        //          "type": "object",
        //          "properties": {
        //              "name": {
        //                  "type": "string",
        //                  "description": "A tag associated with the meeting for categorization."
        //              }
        //          }
        //      },
        //      "description": "A list of tags to help categorize the meeting."
        //  }

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["subject"] = "IT Meeting",
            ["start_dateTime"] = "2023-10-01T10:00:00",
            ["start_timeZone"] = "UTC",
            ["end_dateTime"] = "2023-10-01T11:00:00",
            ["end_timeZone"] = "UTC",
            ["tags"] = """[ { "name": "IT" }, { "name": "Meeting" }  ]"""
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        AzureOpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload root properties.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadRootPropertiesAsync()
    {
        // Create an Open API document for the Event Utils service
        using MemoryStream document = CreateOpenApiDocumentForEventUtilsService();

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", document, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true, // Enable dynamic payload construction. It is enabled by default.
            UseRootPropsForDynamicPayload = true // Use root properties for dynamic payload construction
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "subject"
        //   Description: "The subject or title of the meeting."
        //   ParameterType: { Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The subject or title of the meeting." }
        // Parameter[1]
        //   Name: "start"
        //   Description: "The start details of the meeting, including date and time."
        //   ParameterType: {Name = "Object" FullName = "System.Object"}
        //   Schema: {
        //      "required": ["dateTime", "timeZone"],
        //      "type": "object",
        //      "properties": {
        //          "dateTime": {
        //              "type": "string",
        //              "description": "The start date and time of the meeting in ISO 8601 format.",
        //              "format": "date-time"
        //          },
        //          "timeZone": {
        //              "type": "string",
        //              "description": "The time zone in which the meeting starts."
        //          }
        //      }
        //  }
        // Parameter[2]
        //   Name: "end"
        //   Description: "The end details of the meeting, including date and time."
        //   ParameterType: {Name = "Object" FullName = "System.Object"}
        //   Schema: Similar to the 'start' property one
        // Parameter[3]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        //   Schema: {
        //      "type": "array",
        //      "items": {
        //          "required": ["name"],
        //          "type": "object",
        //          "properties": {
        //              "name": {
        //                  "type": "string",
        //                  "description": "A tag associated with the meeting for categorization."
        //              }
        //          }
        //      },
        //      "description": "A list of tags to help categorize the meeting."
        //  }

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["subject"] = "IT Meeting",
            ["start"] = """{ "dateTime": "2023-10-01T10:00:00", "timeZone": "UTC" }""",
            ["end"] = """{ "dateTime": "2023-10-01T11:00:00", "timeZone": "UTC" }""",
            ["tags"] = """[ { "name": "IT" }, { "name": "Meeting" }  ]"""
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        AzureOpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates detection of circular references in the OpenAPI document.
    /// </summary>
    [Fact]
    public async Task ImportOpenApiFunctionWithCircularReferencesInDefinitionWithArgumentsForPayloadLeafPropertiesAsync()
    {
        // Create an Open API document for the simplified Event Utils service
        using MemoryStream document = CreateOpenApiDocumentWithCircularReferencesForEventUtilsService();

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", document, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true, // Enable dynamic payload construction. It is enabled by default.
            EnablePayloadNamespacing = true // Enable payload namespacing.
        });
    }

    private static MemoryStream CreateOpenApiDocumentForSimplifiedEventUtilsService()
    {
        var document = """
        {  
          "openapi": "3.0.1",  
          "info": {  
            "title": "Event Utils API",  
            "version": "1.0.0",  
            "description": "API for managing events."  
          },  
          "servers": [  
            {  
              "url": "https://api.yourdomain.com"  
            }  
          ],  
          "paths": {  
            "/meetings": {  
              "put": {  
                "summary": "Create a meeting",  
                "description": "Creates a new meeting.",  
                "operationId": "createMeeting",  
                "requestBody": {  
                  "required": true,  
                  "content": {  
                    "application/json": {  
                      "schema": {  
                        "type": "object",  
                        "properties": {  
                          "subject": {  
                            "type": "string",  
                            "description": "The subject or title of the meeting."  
                          },  
                          "start": {  
                            "type": "object",  
                            "properties": {  
                              "dateTime": {  
                                "type": "string",  
                                "format": "date-time",  
                                "description": "The start date and time of the meeting in ISO 8601 format."  
                              },  
                              "timeZone": {  
                                "type": "string",  
                                "description": "The time zone in which the meeting is scheduled."  
                              }  
                            },  
                            "required": [  
                              "dateTime",  
                              "timeZone"  
                            ]  
                          },  
                          "duration": {  
                            "type": "string",  
                            "description": "Duration of the meeting in ISO 8601 format (e.g., 'PT1H' for 1 hour)."  
                          },  
                          "tags": {  
                            "type": "array",  
                            "items": {  
                              "type": "object",  
                              "properties": {  
                                "name": {  
                                  "type": "string",  
                                  "description": "A tag associated with the meeting for categorization."  
                                }  
                              },  
                              "required": [  
                                "name"  
                              ]  
                            },  
                            "description": "A list of tags to help categorize the meeting."  
                          }  
                        },  
                        "required": [  
                          "subject",  
                          "start",  
                          "duration",  
                          "tags"  
                        ]  
                      }  
                    }  
                  }  
                },  
                "responses": {  
                  "200": {  
                    "description": "Meeting created successfully.",  
                    "content": {  
                      "application/json": {  
                        "schema": {  
                          "type": "object",  
                          "properties": {  
                            "id": {  
                              "type": "string",  
                              "description": "The unique identifier for the meeting."  
                            }  
                          },  
                          "required": [  
                            "id"  
                          ]  
                        }  
                      }  
                    }  
                  }  
                }  
              }  
            }  
          }  
        }  
        
        """;

        return new MemoryStream(Encoding.UTF8.GetBytes(document));
    }

    private static MemoryStream CreateOpenApiDocumentForEventUtilsService()
    {
        var document = """
        {  
          "openapi": "3.0.1",  
          "info": {  
            "title": "Event Utils API",  
            "version": "1.0.0",  
            "description": "API for managing events."  
          },  
          "servers": [  
            {  
              "url": "https://api.yourdomain.com"  
            }  
          ],  
          "paths": {  
            "/meetings": {  
              "put": {  
                "summary": "Create a meeting",  
                "description": "Creates a new meeting.",  
                "operationId": "createMeeting",  
                "requestBody": {  
                  "required": true,  
                  "content": {  
                    "application/json": {  
                      "schema": {  
                        "type": "object",  
                        "properties": {  
                          "subject": {  
                            "type": "string",  
                            "description": "The subject or title of the meeting."  
                          },  
                          "start": {  
                            "type": "object",  
                            "description": "The start details of the meeting, including date and time.",  
                            "properties": {  
                              "dateTime": {  
                                "type": "string",  
                                "format": "date-time",  
                                "description": "The start date and time of the meeting in ISO 8601 format."  
                              },  
                              "timeZone": {  
                                "type": "string",  
                                "description": "The time zone in which the meeting starts."  
                              }  
                            },  
                            "required": [  
                              "dateTime",  
                              "timeZone"  
                            ]  
                          },  
                          "end": {  
                            "type": "object",  
                            "description": "The end details of the meeting, including date and time.",  
                            "properties": {  
                              "dateTime": {  
                                "type": "string",  
                                "format": "date-time",  
                                "description": "The end date and time of the meeting in ISO 8601 format."  
                              },  
                              "timeZone": {  
                                "type": "string",  
                                "description": "The time zone in which the meeting ends."  
                              }  
                            },  
                            "required": [  
                              "dateTime",  
                              "timeZone"  
                            ]  
                          },  
                          "tags": {  
                            "type": "array",  
                            "items": {  
                              "type": "object",  
                              "properties": {  
                                "name": {  
                                  "type": "string",  
                                  "description": "The name of the tag associated with the meeting."  
                                }  
                              },  
                              "required": [  
                                "name"  
                              ]  
                            },  
                            "description": "A list of tags associated with the meeting for categorization."  
                          }  
                        },  
                        "required": [  
                          "subject",  
                          "start",  
                          "end",  
                          "tags"  
                        ]  
                      }  
                    }  
                  }  
                },  
                "responses": {  
                  "200": {  
                    "description": "Meeting created successfully.",  
                    "content": {  
                      "application/json": {  
                        "schema": {  
                          "type": "object",  
                          "properties": {  
                            "id": {  
                              "type": "string",  
                              "description": "The unique identifier for the meeting."  
                            }  
                          },  
                          "required": [  
                            "id"  
                          ]  
                        }  
                      }  
                    }  
                  }  
                }  
              }  
            }  
          }  
        }  
        """;

        return new MemoryStream(Encoding.UTF8.GetBytes(document));
    }

    private static MemoryStream CreateOpenApiDocumentWithCircularReferencesForEventUtilsService()
    {
        var document = """
        {
          "openapi": "3.0.1",
          "info": {
            "title": "Event Utils API",
            "version": "1.0.0",
            "description": "API for managing events."
          },
          "servers": [
            {
              "url": "https://api.yourdomain.com"
            }
          ],
          "paths": {
            "/meetings": {
              "put": {
                "summary": "Create a meeting",
                "description": "Creates a new meeting.",
                "operationId": "createMeeting",
                "requestBody": {
                  "required": true,
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/Meeting"
                      }
                    }
                  }
                },
                "responses": {
                  "200": {
                    "description": "Meeting created successfully.",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "object",
                          "properties": {
                            "id": {
                              "type": "string",
                              "description": "The unique identifier for the meeting."
                            }
                          },
                          "required": [
                            "id"
                          ]
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "components": {
            "schemas": {
              "Meeting": {
                "type": "object",
                "properties": {
                  "subject": {
                    "type": "string",
                    "description": "The subject or title of the meeting."
                  },
                  "start": {
                    "type": "object",
                    "description": "The start details of the meeting, including date and time.",
                    "properties": {
                      "dateTime": {
                        "type": "string",
                        "format": "date-time",
                        "description": "The start date and time of the meeting in ISO 8601 format."
                      },
                      "timeZone": {
                        "type": "string",
                        "description": "The time zone in which the meeting starts."
                      }
                    },
                    "required": [
                      "dateTime",
                      "timeZone"
                    ]
                  },
                  "end": {
                    "type": "object",
                    "description": "The end details of the meeting, including date and time.",
                    "properties": {
                      "dateTime": {
                        "type": "string",
                        "format": "date-time",
                        "description": "The end date and time of the meeting in ISO 8601 format."
                      },
                      "timeZone": {
                        "type": "string",
                        "description": "The time zone in which the meeting ends."
                      }
                    },
                    "required": [
                      "dateTime",
                      "timeZone"
                    ]
                  },
                  "tags": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "name": {
                          "type": "string",
                          "description": "The name of the tag associated with the meeting."
                        }
                      },
                      "required": [
                        "name"
                      ]
                    },
                    "description": "A list of tags associated with the meeting for categorization."
                  },
                  "createdBy": {
                    "$ref": "#/components/schemas/Attendee"
                  }
                },
                "required": [
                  "subject",
                  "start",
                  "end",
                  "tags",
                  "createdBy"
                ]
              },
              "Attendee": {
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string",
                    "description": "The name of the attendee."
                  },
                  "meeting": {
                    "$ref": "#/components/schemas/Meeting",
                    "description": "The meeting the attendee is associated with."
                  }
                },
                "required": [
                  "name"
                ]
              }
            }
          }
        }
        """;

        return new MemoryStream(Encoding.UTF8.GetBytes(document));
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        this._httpClient.Dispose();
    }

    private sealed class StubHttpHandler : DelegatingHandler
    {
        private readonly Action<string> _requestPayloadHandler;
        private readonly JsonSerializerOptions _options;

        public StubHttpHandler(Action<string> requestPayloadHandler) : base()
        {
            this._requestPayloadHandler = requestPayloadHandler;
            this._options = new JsonSerializerOptions { WriteIndented = true };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage? request, CancellationToken cancellationToken)
        {
            var requestJson = await request!.Content!.ReadFromJsonAsync<JsonElement>(cancellationToken);

            this._requestPayloadHandler(JsonSerializer.Serialize(requestJson, this._options));

            return new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("Success", Encoding.UTF8, "application/json")
            };
        }
    }
}
