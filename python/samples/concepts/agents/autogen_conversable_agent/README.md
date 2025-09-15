## AutoGen Conversable Agent (v0.2.X)

Semantic Kernel Python supports running AutoGen Conversable Agents provided in the 0.2.X package.

### Limitations

Currently, there are some limitations to note:

- AutoGen Conversable Agents in Semantic Kernel run asynchronously and do not support streaming of agent inputs or responses.

### Installation

Install the `semantic-kernel` package with the `autogen` extra:

```bash
pip install semantic-kernel[autogen]
```

For an example of how to integrate an AutoGen Conversable Agent using the Semantic Kernel Agent abstraction, please refer to [`autogen_conversable_agent_simple_convo.py`](autogen_conversable_agent_simple_convo.py).