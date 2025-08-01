# Summary

This demo showcases the ability to parse a YAML workflow based on Copilo Studio actions
and produce a `KernelProcess` that can be executed in the same fashion as any other `KernelProcess`.

## Key Features

This demo illustrates the following capabilities:

- Parse YAML workflow actions using `Microsoft.Bot.ObjectModel`
- Store and retrieve variable state
- Evaluate expressions using `Microsoft.PowerFx.Interpreter`
- Support control flow (foreach, goto, etc...)
- Generate response from LLM using _Semantic Kernel_

## Status Details

- This is using a POC based on the _Process Framework_ from the _Semantic Kernel_ repo.
  - When the redesigned _Process Framework_ is available in the _Agent Framework_ repo it must 
    be re-implemented using the new API patterns.
  - Capturing and restoring workflow state is not yet available in either version of the _Process Framework_.
  - The ability to emit events from the _KernelProcess_ to the host API is not yet supported.
- `Microsoft.Bot.ObjectModel` is not (yet) available as a dependency that may be referenced by a _GitHub_ repository.
- The full set of CPSDL actions to be supported is not fully defined, nor are the "Pri-0" samples.
