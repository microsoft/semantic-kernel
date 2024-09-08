# Achieving Feature Parity in Python and C#

This is a high-level overview of where things stand towards reaching feature parity with the main
 [C# codebase](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/SemanticKernel).

|      |      |       |
|------|------| ------
|      |Python| Notes |
|`./ai/embeddings`| 🔄| Using Numpy for embedding representation. Vector operations not yet implemented |
|`./ai/openai`| 🔄 | Makes use of the OpenAI Python package. AzureOpenAI* not implemented |
|`./configuration`|✅ | Direct port. Check inline docs |
|`./core_skills`| 🔄 | `TextMemorySkill` implemented. Others not |
|`./diagnostics` | ✅ | Direct port of custom exceptions and validation helpers |
|`./kernel_extensions` | 🔄 | Extensions take kernel as first argument and are exposed via `sk.extensions.*`
|`./memory`| 🔄 | Can simplify by relying on Numpy NDArray
|`./planning`| ❌ | Not yet implemented
|`./semantic_functions/partitioning`| ❌ | Not yet implemented


## Status of the Port

The port has a bulk of the Semantic Kernel C# code re-implemented, but is not yet fully complete. Major things like `tests` and `docs` are still missing.
Here is a breakdown by sub-module on the status of this port:

### `./ai/embeddings` (Partial) 

For now, `VectorOperations` from the original kernel will be skipped. We can use
`numpy`'s `ndarray` as an efficient embedding representation. We can also use 
`numpy`'s optimized vector and matrix operations to do things like cosine similarity
quickly and efficiently.

The `IEmbeddingIndex` interface has been translated to the `EmbeddingIndexBase` abstract
class. The `IEmbeddingGenerator` interface has been translated to the 
`embedding_generator_base` abstract class.

The C# code makes use of extension methods to attach convenience methods to many interfaces
and classes. In Python we don't have that luxury. Instead, these methods are in the corresponding class definition.
(We can revisit this, but for good type hinting avoiding something fancy/dynamic works best.)

### `./ai/openai` (Partial)

The abstract clients (`(Azure)OpenAIClientAbstract`) have been ignored here. The `HttpSchema`
submodule is not needed given we have the `openai` package to do the heavy lifting (bonus: that
package will stay in-sync with OpenAI's updates, like the new ChatGPT API).

The `./ai/openai/services` module is retained and has the same classes/structure.

#### TODOs

The `AzureOpenAI*` alternatives are not yet implemented. This would be a great, low difficulty
task for a new contributor to pick up.

### `./ai` (Complete?)

The rest of the classes at the top-level of the `./ai` module have been ported
directly. 

**NOTE:** here, we've locked ourselves into getting a _single_ completion
from the model. This isn't ideal. Getting multiple completions is sometimes a great
way to solve more challenging tasks (majority voting, re-ranking, etc.). We should look
at supporting multiple completions.

**NOTE:** Based on `CompleteRequestSettings` no easy way to grab the `logprobs`
associated with the models completion. This would be huge for techniques like re-ranking
and also very crucial data to capture for metrics. We should think about how to 
support this. (We're currently a "text in text out" library, but multiple completions
and logprobs seems to be fundamental in this space.)

### `./configuration` (Complete?)

Direct port, not much to do here. Probably check for good inline docs.

### `./core_skills` (Partial)

We've implemented the `TextMemorySkill` but are missing the following:

- `ConversationSummarySkill`
- `FileIOSkill`
- `HttpSkill`
- `PlannerSkill` (NOTE: planner is a big sub-module we're missing)
- `TextSkill`
- `TimeSkill`

#### TODOs

Any of these individual core skills would be create low--medium difficulty contributions
for those looking for something to do. Ideally with good docs and corresponding tests.

### `./diagnostics` (Complete?)

Pretty direct port of these few custom exceptions and validation helpers.

### `./kernel_extensions` (Partial)

This is difficult, for good type hinting there's a lot of duplication. Not having the 
convenience of extension methods makes this cumbersome. Maybe, in the future, we may
want to consider some form of "plugins" for the kernel?

For now, the kernel extensions take the kernel as the first argument and are exposed
via the `sk.extensions.*` namespace.

### `./memory` (Partial)

This was a complex sub-system to port. The C# code has lots of interfaces and nesting
of types and generics. In Python, we can simplify this a lot. An embedding
is an `ndarray`. There's lots of great pre-built features that come with that. The
rest of the system is a pretty direct port but the layering can be a bit confusing. 
I.e. What's the real difference between storage, memory, memory record,
data entry, an embedding, a collection, etc.? 

#### TODOs

Review of this subsystem. Lots of good testing. Maybe some kind of overview 
documentation about the design. Maybe a diagram of how all these classes and interfaces
fit together?

### `./orchestration` (Complete?)

This was a pretty core piece and another direct port. Worth double checking. Needs good docs and tests.

### `./planning` (TODO: nothing yet)

Completely ignored planning for now (and, selfishly, planning isn't a priority for 
SK-based experimentation).

### `./reliability` (Complete?)

Direct port. Nothing much going on in this sub-module. Likely could use more strategies
for retry. Also wasn't quite sure if this was integrated with the kernel/backends? 
(Like are we actually using the re-try code, or is it not hit)

#### TODOs

Implement a real retry strategy that has backoff perhaps. Make sure this code is integrated
and actually in use.

### `./semantic_functions` (Complete?)

Another core piece. The different config classes start to feel cumbersome here 
(func config, prompt config, backend config, kernel config, so so much config).

### `./semantic_functions/partitioning` (TODO: nothing yet)

Skipped this sub-sub-module for now. Good task for someone to pick up!

### `./skill_definition` (Complete?)

Another core piece, another pretty direct port. 

**NOTE:** the attributes in C# become decorators in Python. We probably could 
make it feel a bit more pythonic (instead of having multiple decorators have just
one or two). 

**NOTE:** The skill collection, read only skill collection, etc. became a bit 
confusing (in terms of the relationship between everything). Would be good to 
double check my work there.

### `./template_engine` (Complete?)

Love the prompt templates! Have tried some basic prompts, prompts w/ vars,
and prompts that call native functions. Seems to be working.

**NOTE:** this module definitely needs some good tests. There can be see some
subtle errors sneaking into the prompt tokenization/rendering code here.

### `./text` (TODO: nothing yet)

Ignored this module for now.

### `<root>` (Partial)

Have a working `Kernel` and a working `KernelBuilder`. The base interface
and custom exception are ported. the `Kernel` in particular
is missing some things, has some bugs, could be cleaner, etc. 

## Overall TODOs

We are currently missing a lot of the doc comments from C#. So a good review
of the code and a sweep for missing doc comments would be great.

We also are missing any _testing_. We should figure out how we want to test
(I think this project is auto-setup for `pytest`).

Finally, we are missing a lot of examples. It'd be great to have Python notebooks
that show off many of the features, many of the core skills, etc.


## Design Choices

We want the overall design of the kernel to be as similar as possible to C#.
We also want to minimize the number of external dependencies to make the Kernel as lightweight as possible. 

Right now, compared to C# there are two key differences:

1. Use `numpy` to store embeddings and do things like vector/matrix ops
2. Use `openai` to interface with (Azure) OpenAI 

There's also a lot of more subtle differences that come with moving to Python,
things like static properties, no method overloading, no extension methods, etc.
