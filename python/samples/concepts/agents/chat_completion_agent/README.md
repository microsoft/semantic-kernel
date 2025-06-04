# Chat Completion Agent Samples

The following samples demonstrate advanced usage of the `ChatCompletionAgent`.

---

## Chat History Reduction Strategies

When configuring chat history management, there are two important settings to consider:

### `reducer_msg_count`

- **Purpose:** Defines the target number of messages to retain after applying truncation or summarization.
- **Controls:** Determines how much recent conversation history is preserved, while older messages are either discarded or summarized.
- **Recommendations for adjustment:**
    - **Smaller values:** Ideal for memory-constrained environments or scenarios where brief context is sufficient.
    - **Larger values:** Useful when retaining extensive conversational context is critical for accurate responses or complex dialogue.

### `reducer_threshold`

- **Purpose:** Provides a buffer to prevent premature reduction when the message count slightly exceeds `reducer_msg_count`.
- **Controls:** Ensures essential message pairs (e.g., a user query and the assistant’s response) aren't unintentionally truncated.
- **Recommendations for adjustment:**
    - **Smaller values:** Use to enforce stricter message reduction criteria, potentially truncating older message pairs sooner.
    - **Larger values:** Recommended for preserving critical conversation segments, particularly in sensitive interactions involving API function calls or detailed responses.

### Interaction Between Parameters

The combination of these parameters determines **when** history reduction occurs and **how much** of the conversation is retained.

**Example:**
- If `reducer_msg_count = 10` and `reducer_threshold = 5`, message history won't be truncated until the total message count exceeds 15. This strategy maintains conversational context flexibility while respecting memory limitations.

---

## Recommendations for Effective Configuration

- **Performance-focused environments:**
  - Lower `reducer_msg_count` to conserve memory and accelerate processing.
  
- **Context-sensitive scenarios:**
  - Higher `reducer_msg_count` and `reducer_threshold` help maintain continuity across multiple interactions, crucial for multi-turn conversations or complex workflows.

- **Iterative Experimentation:**
  - Start with default values (`reducer_msg_count = 10`, `reducer_threshold = 10`), and adjust according to the specific behavior and response quality required by your application.
