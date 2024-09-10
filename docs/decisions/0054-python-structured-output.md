---
# These are optional elements. Feel free to remove any of them.
status: { in-progress }
contact: { Evan Mattson }
date: { 2024-09-10 }
deciders: { Ben Thomas }
consulted: { Dmytro Struk }
informed: { Eduard van Valkenburg, Ben Thomas, Tao Chen, Dmytro Struk, Mark Wallace }
---

# Supporting OpenAI's Structured Output in Semantic Kernel Python

## Context

Last year, OpenAI introduced JSON mode, an essential feature for developers aiming to build reliable AI-driven applications. While JSON mode helps improve model reliability in generating valid JSON outputs, it falls short of enforcing strict adherence to specific schemas. This limitation has led developers to employ workarounds—such as custom open-source tools, iterative prompting, and retries—to ensure that the output conforms to required formats.

To address this issue, OpenAI has introduced **Structured Outputs**—a feature designed to ensure that model-generated outputs conform precisely to developer-specified JSON Schemas. This advancement allows developers to build more robust applications by providing guarantees that AI outputs will match predefined structures, improving interoperability with downstream systems.

In recent evaluations, the new GPT-4o-2024-08-06 model with Structured Outputs demonstrated a perfect 100% score in adhering to complex JSON schemas, compared to GPT-4-0613, which scored less than 40%. Structured Outputs streamline the process of generating reliable structured data from unstructured inputs, a core need in various AI-powered applications such as data extraction, automated workflows, and function calling.

---

## Problem Statement

Developers building AI-driven solutions using the OpenAI API often face challenges when extracting structured data from unstructured inputs. Ensuring model outputs conform to predefined JSON schemas is critical for creating reliable and interoperable systems. However, current models, even with JSON mode, do not guarantee schema conformity, leading to inefficiencies, errors, and additional development overhead in the form of retries and custom tools.

With the introduction of Structured Outputs, OpenAI models are now able to strictly adhere to developer-provided JSON schemas. This feature eliminates the need for cumbersome workarounds and provides a more streamlined, efficient way to ensure consistency and reliability in model outputs. Integrating Structured Outputs into the Semantic Kernel orchestration SDK will enable developers to create more powerful, schema-compliant applications, reduce errors, and improve overall productivity.

## Using Structured Outputs

### 1. Function Calling

Structured outputs can be used for function calling to ensure adherence to a schema. In Python, using OpenAI's latest SDK, developers can use the `pydantic_function_tool()` method to convert a Pydantic model into the required `structured output` function-calling JSON schema:


```python
client = AsyncOpenAI()

# Note that the SDK method is `client.beta.chat.completions.parse` instead of our current `client.chat.completions.create` call.
completion = await client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant. The current date is August 6, 2024. You help users query for the data they are looking for by calling the query function.",
        },
        {
            "role": "user",
            "content": "look up all my orders in may of last year that were fulfilled but not delivered on time",
        },
    ],
    tools=[
        openai.pydantic_function_tool(SomeClass), # This is a new method provided by OpenAI to handle Pydantic models
    ],
)

print(completion.choices[0].message)
```

This produces the following JSON Schema:

```json
{
  "type": "function",
  "function": {
    "name": "math-add_numbers",
    "description": "Adds two numbers together and provides the result",
    "strict": true, // new key-value pair for structured output function calling
    "parameters": {
      "type": "object",
      "properties": {
        "number_one": {
          "type": "integer",
          "description": "The first number to add"
        },
        "number_two": {
          "type": "integer",
          "description": "The second number to add"
        }
      },
      "required": ["number_one", "number_two"],
      "additionalProperties": false // new key-value pair for structured output function calling
    }
  }
}
```

For non-Pydantic models, SK will need to manually add the `strict` and `additionalProperties` key-value pairs to the JSON schema, which is currently built as part of the `KernelParameterMetadata`.

Additionally, OpenAI states:

"By default, when you use function calling, the API will offer best-effort matching for your parameters, which means that occasionally the model may miss parameters or get their types wrong when using complicated schemas. Structured Outputs is a feature that ensures model outputs for function calls will exactly match your supplied schema. Structured Outputs for function calling can be enabled with a single parameter, just by supplying strict: true."

source: https://platform.openai.com/docs/guides/function-calling/function-calling-with-structured-outputs

When using `structured output` for function calling, we should default the `strict` boolean to true and allow developers to opt-out of the default `strict` behavior when their scenario requires it, such as:

- The developer needs to use unsupported JSON Schema features (e.g., recursive schemas).
- Each API request includes a dynamic schema that may change between requests and is not repeatable.

source: https://platform.openai.com/docs/guides/function-calling/why-might-i-not-want-to-turn-on-structured-outputs

### Structured Output Function Calling Implementation Options

We have two main options to handle configuring the `strict` boolean when generating the JSON Schema for function calling:

1. Kernel Function Decorator 

Allow the developer to define on a kernel function decorator whether that they want it to be handled with the `strict` boolean:

```python
@kernel_function(name="my_function", description="A sample kernel function.", strict_schema=True|False)
    def my_method(self) -> str:
        pass
```

By default, the `strict_schema` would be set to `True`. Developers can toggle it off if necessary. This provides fine-grained control for each kernel function, particularly useful for dynamic or unsupported schemas.

2. FunctionChoiceBehavior 

Allow the developer to specify `strict_schema` on `FunctionChoiceBehavior`, which is part of the prompt execution settings. This method applies the `strict` boolean to all kernel plugins/functions defined, offering less fine-grained control than the first option.

```python
function_choice_behavior=FunctionChoiceBehavior.Auto(strict_schema=True|False)
```

### 2. Response Format

OpenAI also offers a new way to set the `response_format` on the prompt execution settings attribute:

```python
from pydantic import BaseModel

from openai import OpenAI


class Step(BaseModel):
    explanation: str
    output: str


class MathResponse(BaseModel):
    steps: list[Step]
    final_answer: str


client = AsyncOpenAI()

completion = await client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse, # a Pydantic model type is directly configured
)

message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print(message.parsed.final_answer)
else:
    print(message.refusal)
```

For non-Pydantic models, SK will need to use the `KernelParameterMetadata`'s `schema_data` attribute. This represents the JSON Schema of the SK function:

```json
{
  "type": "object",
  "properties": {
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string"
          },
          "output": {
            "type": "string"
          }
        },
        "required": ["explanation", "output"],
        "additionalProperties": false
      }
    },
    "final_answer": {
      "type": "string"
    }
  },
  "required": ["steps", "final_answer"],
  "additionalProperties": false
}
```

to create the required `json_schema` response format:

```json
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "math_response",
        "strict": true,
        "schema": { // start of existing SK `schema_data`
            "type": "object",
            "properties": {
                "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                    "explanation": {
                        "type": "string"
                    },
                    "output": {
                        "type": "string"
                    }
                    },
                    "required": ["explanation", "output"],
                    "additionalProperties": false
                }
                },
                "final_answer": {
                    "type": "string"
                }
            },
            "required": ["steps", "final_answer"],
            "additionalProperties": false
        } // end of existing SK `schema_data`
    }
}
```

#### Handling the Streaming Response Format

The new `structured output` response format is in beta, and the streaming chat completion code should be handled like this (which is different than our current streaming chat completion call):

```python
async with client.beta.chat.completions.stream(
    model='gpt-4o-mini',
    messages=messages,
    tools=[pydantic_function_tool(SomeClass)],
) as stream:
    async for event in stream:
        if event.type == 'content.delta':
            print(event.delta, flush=True, end='')
        elif event.type == 'content.done':
            content = event.content
        elif event.type == 'tool_calls.function.arguments.done':
            tool_calls.append({'name': event.name, 'parsed_arguments': event.parsed_arguments})

print(content)
```

The `OpenAIHandler` class, which manages chat completions, will need to handle the new structured output streaming method, similar to:

```python
async def _initiate_chat_stream(self, settings: OpenAIChatPromptExecutionSettings):
    """Initiate the chat stream request and return the stream."""
    return self.client.beta.chat.completions.stream(
        model='gpt-4o-mini',
        messages=settings.messages,
        tools=[pydantic_function_tool(SomeClass)],
    )

async def _handle_chat_stream(self, stream):
    """Handle the events from the chat stream."""
    async for event in stream:
        if event.type == 'content.delta':
            chunk_metadata = self._get_metadata_from_streaming_chat_response(event)
            yield [
                self._create_streaming_chat_message_content(event, event.delta, chunk_metadata)
            ]
        elif event.type == 'tool_calls.function.arguments.done':
            # Handle tool call results as needed
            tool_calls.append({'name': event.name, 'parsed_arguments': event.parsed_arguments})

# An example calling method could be:
async def _send_chat_stream_request(self, settings: OpenAIChatPromptExecutionSettings):
    """Send the chat stream request and handle the stream."""
    async with await self._initiate_chat_stream(settings) as stream:
        async for chunk in self._handle_chat_stream(stream):
            yield chunk
```

The method for handling the stream or non-streaming chat completion will be based on the `response_format` execution setting -- whether it uses a Pydantic model type or a JSON Schema.

Since the `response_format` chat completion method differs from the current chat completion approach, we will need to maintain separate implementations for handling chat completions until OpenAI officially integrates the `response_format` method into the main library upon its graduation.

### Callouts

- The `structured output` `response_format` is limited to a single object type at this time. We will use a Pydantic validator to make sure a user is only specifying the proper type/amount:

```python
@field_validator("response_format", mode="before")
    @classmethod
    def validate_response_format(cls, value):
        """Validate the response_format parameter."""
        if not isinstance(value, dict) and not (isinstance(value, type) and issubclass(value, BaseModel)):
            raise ServiceInvalidExecutionSettingsError(
                "response_format must be a dictionary or a single Pydantic model class"
            )
        return value
```

### Chosen Solution

There are two methods to support structured outputs in Semantic Kernel: function calling and response_format.

- Function Calling: We will introduce the ability to handle a new key-value pair within the kernel function decorator. This will provide fine-grained control, allowing developers to specify whether a given Semantic Kernel function should adhere to the strict schema or not.
- Response Format: Since there's a single approach here, we should integrate a clean implementation to define both streaming and non-streaming chat completions using our existing `OpenAIChatCompletionBase` and `OpenAIHandler` code.
