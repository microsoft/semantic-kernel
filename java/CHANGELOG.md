# 1.1.1

- Upgrade azure-ai-openai to 1.0.0-beta.8

# 1.1.0

### Breaking Changes

- `ChatHistory` no longer has a default message, see below for more details.

### Api Changes
  - Allow setting deployment name in addition to modelId on AI services.
  - Remove default message of "Assistant is a large language model" from ChatHistory
    - **This is a breaking change if you were relying on the default message in your code**
  - Add InvocationReturnMode and rework OpenAi chat completion to allow configuring what data is returned from Chat requests

### Other
- Reorganize example projects and documentation structure.
- Number of sample updates and bug fixes.