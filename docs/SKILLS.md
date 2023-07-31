# What are plugins?

This document has been moved to the Semantic Kernel Documentation site. You can find it by navigating to the [Using AI plugins in Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins) page.

A skill refers to a domain of expertise made available to the kernel as a single
function, or as a group of functions related to the skill. The design of SK skills
has prioritized maximum flexibility for the developer to be both lightweight and
extensible.

# What is a Function?

![image](https://user-images.githubusercontent.com/371009/221742673-3ee8abb8-fe10-4669-93e5-5096d3d09580.png)

A function is the basic building block for a skill. A function can be expressed
as either:

1. an LLM AI prompt — also called a "semantic" function
2. native computer code -- also called a "native" function

When using native computer code, it's also possible to invoke an LLM AI prompt —
which means that there can be functions that are hybrid LLM AI × native code as well.

Functions can be connected end-to-end, or "chained together," to create more powerful
capabilities. When they are represented as pure LLM AI prompts in semantic functions,
the word "function" and "prompt" can be used interchangeably.

# What is the relationship between semantic functions and skills?

A skill is the container in which functions live. You can think of a semantic skill
as a directory of folders that contain multiple directories of semantic functions
or a single directory as well.

```
SkillName (directory name)
│
└─── Function1Name (directory name)
│
└─── Function2Name (directory name)
```

Each function directory will have an skprompt.txt file and a config.json file. There's
much more to learn about semantic functions in Building Semantic Functions if you
wish to go deeper.

# What is the relationship between native functions and skills?

Native functions are loosely inspired by Azure Functions and exist as individual
native skill files as in MyNativeSkill.cs below:

```
MyAppSource
│
└───MySkillsDirectory
    │
    └─── MySemanticSkill (a directory)
    |   │
    |   └─── MyFirstSemanticFunction (a directory)
    |   └─── MyOtherSemanticFunction (a directory)
    │
    └─── MyNativeSkill.cs (a file)
    └─── MyOtherNativeSkill.cs (a file)
```

Each file will contain multiple native functions that are associated with a skill.

# Where to find skills in the GitHub repo

Skills are stored in one of three places:

1. Core Skills: these are skills available at any time to the kernel that embody
   a few standard capabilities like working with time, text, files, and http requests.
   The core skills can be found [here](../dotnet/src/Skills/Skills.Core).

2. Semantic Skills: these skills are managed by you in a directory of your choice.

3. Native Skills: these skills are also managed by you in a directory of your choice.

For more examples of skills, and the ones that we use in our sample apps, look inside
the [/prompts/samples](../prompts/samples) folder.
