# Glossary ✍

To wrap your mind around the concepts we present throughout the kernel, here is a glossary of
commonly used terms

**Semantic Kernel (SK)** - The orchestrator that fulfills a user's ASK with SK's available SKILLS.

**Ask**- What a user requests to the Semantic Kernel to help achieve the user's goal.

- "We make ASKs to the SK"

**Skill** - A domain-specific collection made available to the SK as a group of finely-tuned functions.

- "We have a SKILL for using Office better"

**Function** - A computational machine comprised of Semantic AI and/or native code that's available in a SKILL.

- "The Office SKILL has many FUNCTIONs"

**Native Function** - expressed in the conventions of the computing language (Python, C#, Typescript)
and easily integrates with SK

**Semantic Function** - expressed in natural language in a text file "skprompt.txt" using SK's Prompt
Template. Each semantic function is defined by a unique prompt template file, developed using modern
**prompt engineering** techniques.

The kernel is designed to encourage **function composition**, allowing users to combine multiple functions
(native and semantic) into a single pipeline.

<p align="center">
<img width="682" alt="image" src="https://user-images.githubusercontent.com/146438/213325811-5ae79e9c-dc5b-4fd1-b85c-e10004a70f29.png">
</p>
