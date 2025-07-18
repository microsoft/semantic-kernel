# Declarative Process Workflows

### Goal

Use the _Process Framework_ to execute a workflow defined with _Copilot Studio Declarative Language_ (CPSDL).


### Requirements

- Translate a workflow defined in CPSDL into a _Process_ for execution.
- Host the resulting _Process_ workflow in the same runtime as any other _Process_.


### Dependencies

Outside of the _Process Framework_, the following packages are utilized to parse and define a workflow based on CSPDL:

- `Microsoft.Bot.ObjectModel`
- `Microsoft.PowerFx.Interpreter`


### Inputs

The runtime is expected to provide the following inputs:

- Host Context: Configuration and channels provided by the runtime. 
- Workflow Definition: A declarative YAML workflow that defines CPSDL actions.
- Task: User / application input that informs workflow execution.


### Invocation Pattern

The only consideration for hosting a workflow process based on CSPDL that differs from 
a pro-code workflow is how the builder is invoked:

```c#
// Context defined by the runtime to provide configuration and channels
HostingContext hostContext = ...;
// Customer defined CPSDL workflow as YAML string
string yamlText = ...;
// User input specific to this workflow execution
string inputMessage = "Why is the sky blue?";

// Parse the CPSDL yaml and provide the resulting KernelProcess instance
// This is should be the _only_ difference compared to running a "pro-code" process
KernelProcess process = ObjectModelBuilder.Build(yamlText, hostContext);

// Execute process with CPSDL specific extension
process.StartAsync(inputMessage);
```

### Open Issues

- **Schema Versioning:**
  
  How will the runtime associate workflows defined with different versions of the CPSDL object model with the appropriate builder?
  
  Is this distinction necessary if object model maintains backward compatibility?