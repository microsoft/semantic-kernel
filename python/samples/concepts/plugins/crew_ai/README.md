# Crew AI Plugin for Semantic Kernel

This sample demonstrates how to integrate with [Crew AI Enterprise](https://app.crewai.com/) crews in Semantic Kernel.

## Requirements

Before running this sample you need to have a Crew deployed to the Crew AI Enterprise cloud. Many pre-built Crew templates can be found [here](https://app.crewai.com/crewai_plus/templates). You will need the following information from your deployed Crew:

- endpoint: The base URL for your Crew.
- authentication token: The authentication token for your Crew
- required inputs: Most Crews have a set of required inputs that need to provided when kicking off the Crew and those input names, types, and values need to be known.

- ## Using the Crew Plugin

Once configured, the `CrewAIEnterprise` class can be used directly by calling methods on it, or can be used to generate a Semantic Kernel plugin with inputs that match those of your Crew. Generating a plugin is useful for scenarios when you want an LLM to be able to invoke your Crew as a tool.

## Running the sample

1. Deploy your Crew to the Crew Enterprise cloud.
1. Gather the required information listed above.
1. Create environment variables or use your .env file to define your Crew's endpoint and token as:

```md
CREW_AI_ENDPOINT="{Your Crew's endpoint}"
CREW_AI_TOKEN="{Your Crew's authentication token}"
```

1. In [crew_ai_plugin.py](./crew_ai_plugin.py) find the section that defines the Crew's required inputs and modify it to match your Crew's inputs. The input descriptions and types are critical to help LLMs understand the inputs semantic meaning so that it can accurately call the plugin. The sample is based on the `Enterprise Content Marketing Crew` template which has two required inputs, `company` and `topic`.

```python
    # The required inputs for the Crew must be known in advance. This example is modeled after the
    # Enterprise Content Marketing Crew Template and requires string inputs for the company and topic.
    # We need to describe the type and purpose of each input to allow the LLM to invoke the crew as expected.
    crew_plugin_definitions = [
        KernelParameterMetadata(
            name="company",
            type="string",
            description="The name of the company that should be researched",
            is_required=True,
        ),
        KernelParameterMetadata(
            name="topic", type="string", description="The topic that should be researched", is_required=True
        ),
    ]
```

1. Run the sample. Notice that the sample invokes (kicks-off) the Crew twice, once directly by calling the `kickoff` method and once by creating a plugin and invoking it.
