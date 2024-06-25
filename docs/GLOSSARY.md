# Glossary ✍

To wrap your mind around the concepts we present throughout the kernel, here is a glossary of
commonly used terms

**Semantic Kernel (SK)** - The orchestrator that fulfills a user's ASK with SK's available [PLUGINS](PLUGINS.md).

**Ask** - What a user requests to the Semantic Kernel to help achieve the user's goal.

- "We make ASKs to the SK"

**Plugins** - A domain-specific collection made available to the SK as a group of finely-tuned functions.

- "We have a PLUGIN for using Office better"

**Function** - A computational machine comprised of Semantic AI and/or native code that's available in a [PLUGIN](PLUGINS.md).

- "The Office PLUGIN has many FUNCTIONS"

**Native Function** - expressed with traditional computing language (C#, Python, Typescript)
and easily integrates with SK

**Semantic Function** - expressed in natural language in a text file "*skprompt.txt*" using SK's
[Prompt Template language](PROMPT_TEMPLATE_LANGUAGE.md).
Each semantic function is defined by a unique prompt template file, developed using modern
**prompt engineering** techniques.

**Memory** - a collection of semantic knowledge, based on facts, events, documents, indexed with **[embeddings](EMBEDDINGS.md)**.

<p align="center">
<img width="682" alt="image" src="https://user-images.githubusercontent.com/371009/221690406-caaff98e-87b5-40b7-9c58-cfa9623789b5.png">
</p>

The kernel is designed to encourage **function composition**, allowing users to combine multiple functions
(native and semantic) into a single pipeline.

<p align="center">
<img width="682" alt="image" src="https://user-images.githubusercontent.com/371009/221690156-3f90a8c9-ef90-46f7-a097-beb483656e97.png">
</p>
