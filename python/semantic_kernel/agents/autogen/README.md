## AutoGen Conversable Agent (v0.2.X)

Semantic Kernel Python supports running AutoGen Conversable Agents provided in the 0.2.X package.

### Limitations

Currently, there are some limitations to note:

- AutoGen Conversable Agents in Semantic Kernel run asynchronously and do not support streaming of agent inputs or responses.
- The `AutoGenConversableAgent` in Semantic Kernel Python cannot be configured as part of a Semantic Kernel `AgentGroupChat`. As we progress towards GA for our agent group chat patterns, we will explore ways to integrate AutoGen agents into a Semantic Kernel group chat scenario.

### Installation

Install the `semantic-kernel` package with the `autogen` extra:

```bash
pip install semantic-kernel[autogen]
```

For an example of how to integrate an AutoGen Conversable Agent using the Semantic Kernel Agent abstraction, please refer to [`autogen_conversable_agent_simple_convo.py`](../../../samples/concepts/agents/autogen_conversable_agent/autogen_conversable_agent_simple_convo.py).