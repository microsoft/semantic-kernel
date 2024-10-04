---
# These are optional elements. Feel free to remove any of them.
status: { in-progress }
contact: { Evan Mattson }
date: { 2024-09-10 }
deciders: { Ben Thomas }
consulted: { Dmytro Struk }
informed:
  { Eduard van Valkenburg, Ben Thomas, Tao Chen, Dmytro Struk, Mark Wallace }
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

## Out of scope

This ADR will focus on the `structured outputs` `response_format` and not on the function calling aspect. A subsequent ADR will be created around that in the future.

## Using Structured Outputs

### Response Format

OpenAI offers a new way to set the `response_format` on the prompt execution settings attribute:

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
    response_format=MathResponse, # for example, a Pydantic model type is directly configured
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

to create the required `json_schema` `response_format`:

```json
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "math_response",
        "strict": true,
        "schema": { // start of existing SK `schema_data` from above
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
        } // end of existing SK `schema_data` from above
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

- The `structured output` `response_format` is limited to a single object type at this time. We will use a Pydantic validator to make sure a user is only specifying the proper type/amount of objects:

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

- We need to provide good (and easy-to-find) documentation to let users and developers know which OpenAI/AzureOpenAI models/API-versions support `structured outputs`.

### Chosen Solution

- Response Format: Since there's a single approach here, we should integrate a clean implementation to define both streaming and non-streaming chat completions using our existing `OpenAIChatCompletionBase` and `OpenAIHandler` code.
