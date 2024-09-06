---
# These are optional elements. Feel free to remove any of them.
status: { in-progress }
contact: { Evan Mattson }
date: { 2024-09-05 }
deciders: { Eduard van Valkenburg, Ben Thomas, Tao Chen }
consulted: { Eduard van Valkenburg, Dmytro Struk }
informed: { Eduard van Valkenburg, Ben Thomas, Tao Chen, Dmytro Struk }
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

Structured outputs may be used for function calling so that the schema is adhered to. In Python, using OpenAI's latest SDK, one can use a new method called `pydantic_function_tool()` to convert a Pydantic model to the required `structured output` function calling JSON schema:

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
        openai.pydantic_function_tool(Query), # This is a new method provided by OpenAI to handle Pydantic models
    ],
)

print(completion.choices[0].message)
```

which in turn produces the following JSON Schema:

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

For non-Pydantic models, SK needs to manually add the `strict` and `additionalProperties` key-value pairs to the JSON schema that are currently built as part of the `KernelParameterMetadata` today.

Additionally, OpenAI states:

"By default, when you use function calling, the API will offer best-effort matching for your parameters, which means that occasionally the model may miss parameters or get their types wrong when using complicated schemas. Structured Outputs is a feature that ensures model outputs for function calls will exactly match your supplied schema. Structured Outputs for function calling can be enabled with a single parameter, just by supplying strict: true."

source: https://platform.openai.com/docs/guides/function-calling/function-calling-with-structured-outputs

When working with function calling `structured output`, we should default the `strict` boolean to true, and let developers "opt out" of the default strict behavior if their scenario fits into the following:

- the developer needs to use some features of JSON Schema that is not yet supported by OpenAI, for example recursive schemas.
- if each API request includes a dynamic schema -- one that may change between requests and is not repeatable.

source: https://platform.openai.com/docs/guides/function-calling/why-might-i-not-want-to-turn-on-structured-outputs

### Structured Output Function Calling Implementation Options

We have a few options to best handle the the ability to configure the `strict` boolean when generating the JSON Schema tool object for function calling:

1. Allow the developer to define on a kernel function decorator that they want it to be handled with the `strict` boolean:

```python
@kernel_function(name="my_function", description="A sample kernel function.", strict_schema=True|False)
    def my_method(self) -> str:
        pass
```

As mentioned above, we can default that `strict_schema` as `True` and a developer can toggle it off via the `strict_schema` parameter if desired.

By allowing the developer to toggle the `strict_schema`, we allow each kernel function to either follow the strict JSON schema or not. This gives more fine-grained control, and can help if a developer has a dynamic schema or one that is not yet supported, as mentioned above.

2. Allow the developer to specify `strict_schema` as `True|False` on `FunctionChoiceBehavior`, part of the prompt execution settings.

This method does not provide as fine-grained control as the first method since we will apply the `strict` boolean on all kernel plugins/functions defined.

```python
function_choice_behavior=FunctionChoiceBehavior.Auto(strict_schema=True|False)
```

### 2. Response Format

As a second way to dealing with `structured output` OpenAI allows for a new way to set the `response_format` attribute.

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

Similar to handling non-Pydantic models for function calling, SK will need to use the `KernelParameterMetadata`'s `schema_data` attribute:

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

to create the response format in the following way:

```json
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "math_response",
        "strict": true,
        "schema": { // start of `schema_data`
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
        } // end of `schema_data`
    }
}
```

#### Handling Streaming Response Format

Given that the new response format is used via a beta library feature, the streaming chat completion needs to be handled in the following way:

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

This will require different handling in the `OpenAIHandler` class which currently handles a chat completion, both for streaming and non-streaming, in the following way:
