# Multi-agent Orchestration

## Brainstorming

- Support ability to allow devs to create custom patterns for orchestrating multiple SK agents
  - Well-defined building blocks for custom patterns
  - Naming: container?

- Use those building blocks to build out-of-the-box patterns
  - Built-in patterns
    - Concurrent (Broadcast)
    - Sequential (Handoff\*)
    - GroupChat
      - Magentic
      - Swarm

- Support multiple invocation paradigms
  - One pattern can be invoked multiple times*?
    - Stateless patterns: each invocation is independent
    - Stateful patterns: future invocations have context from previous invocations
    - Both?
  - Patterns are graph-like structures with "lazy eval"

- Completion of patterns
  - Return the final result when the pattern finishes
    - Non-blocking: return immediately and broadcast result when the pattern finishes
    - Blocking: wait for the pattern to finish and return the result

- Support nested patterns
  - Pattern abstraction: same invocation signature
  - Patterns to take SK agents and patterns as child nodes

- Patterns should only depend upon the runtime abstraction
  - The runtime must be provided when the pattern is invoked.
  - The runtime lifecycle is managed by the application (external to the pattern).
  - Should a runtime instance be shared between patterns that are supposed to be independent?

- Runtime registration
  - Agents
    - Register the agents and patterns in the runtime before the execution starts.
  - Topics
    - Add subscriptions to the runtime before the execution starts.
  - Make sure no collisions
  - Remove registrations and subscriptions from the runtime after the execution finishes to avoid name collisions.

- Input to patterns
  - a list of tasks (string?) with a context object that contains additional attributes

- Support arbitrary user-defined output types
  - User can define what object a pattern will output at the end
  - Nested pattern: output of a pattern is the input of another

- User proxy
  - Keep the user in the loop and allow them to intervene in the orchestration process

- Save states and rehydration
  - Being able to save the state of the orchestration process while waiting for user input and restore it later when user provides input for scalability
  - Recursively save the state of all agents and child patterns, including threads, chat history, and context from the root pattern

- Support declarative patterns*
