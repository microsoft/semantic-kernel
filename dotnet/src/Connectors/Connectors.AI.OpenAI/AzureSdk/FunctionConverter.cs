// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
internal class FunctionConverter
{
    public static FunctionDefinition ToFunctionDefinition(FunctionView functionView)
    {
        var functionDefinition = new FunctionDefinition
        {
            Name = string.Join(".", functionView.SkillName, functionView.Name),
            Description = functionView.Description,
            /*Parameters = BinaryData.FromObjectAsJson(
                new
                {
                    parameters = new
                    {
                        type = "object",
                        properties = new
                        {
                            param1 = new
                            {
                                type = "",
                                description = ""
                            },
                            param2 = new
                            {
                                type = "",
                                description = ""
                            },
                            required = new[] { param1.name }
                        }
                    }
                }),*/
        };


        var parameterView = functionView.Parameters.First();

        BinaryData data = BinaryData.FromObjectAsJson(
                new
                {
                    parameters = new
                    {
                        type = "object",
                        properties = new
                        {
                            param1 = new
                            {
                                type = "",
                                description = ""
                            },
                            param2 = new
                            {
                                type = "",
                                description = ""
                            },
                            required = new[] { "param1.name" }
                        }
                    }
                });

        //BinaryData.FromString
        //BinaryData.FromObjectAsJson

        /*
        "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
            "type": "object",
                "properties": {
                "location": {
                    "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": { "type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        */

        return functionDefinition;
    }
}
