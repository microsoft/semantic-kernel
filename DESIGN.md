# Design Doc (Python Semantic Kernel)

Right now, in this repository you'll find a Python implementation of the Semantic Kernel.
This implementation is mostly a direct translation of the original C# implementation with
some changes to accommodate the Python language (and leverage great, widely used, packages
like OpenAI's `openai` Python package and `numpy`).

## What can you do right now?

Right now, we have three end-to-end examples working.
You can try running any of:

- `./tests/basic.py`
- `./tests/chat.py`
- `./tests/memory.py`

To get these to work, you'll need a `.env` file
in the root of the repository with the your 
OpenAI API key. **TODO:** grab from `os.environ`
if they exist, use `.env` as backup.

## Status of the Port

The port has a bulk of the Semantic Kernel C# code re-implemented, but is not yet fully complete. Major things like tests and docs are still missing. Here
is a breakdown by sub-module on the status of this port:

### `./ai/embeddings` (Partial) 

For now, `VectorOperations` from the original kernel will be skipped. We can use
`numpy`'s `ndarray` as an efficient embedding representation. We can also use 
`numpy`'s optimized vector and matrix operations to do things like cosine similarity
quickly and efficiently.

The `IEmbeddingIndex` interface has been translated to the `EmbeddingIndexBase` abstract
class. The `IEmbeddingGenerator` interface has been translated to the 
`embedding_generator_base` abstract class.

The C# code makes use of extension methods to attach convenience methods to many interfaces
and classes, in Python we don't have that luxury. Instead, I've been moving these methods
into the corresponding class definition. (We can revisit this, but for good type hinting
avoiding something fancy/dynamic works best.)

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

**NOTE:** here, I notice that we've locked ourselves into getting a _single_ completion
from the model. This isn't ideal. Getting multiple completions is sometimes a great
way to solve more challenging tasks (majority voting, re-ranking, etc.). We should look
at supporting multiple completions.

**NOTE:** I see, based on `CompleteRequestSettings` no easy way to grab the `logprobs`
associated with the models completion. This would be huge for techniques like re-ranking
and also very crucial data to capture for metrics. We should think about how to 
support this. (I know that we're a "text in text out" library, but multiple completions
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
of types and generics... in Python, I think we can simplify this a lot. An embedding
is an `ndarray`. There's lots of great pre-built features that come with that. The
rest of the system is a pretty direct port but I will say that the layering here
is confusing. What's the real difference between storage, memory, memory record,
data entry, an embedding, a collection, etc.? 

#### TODOs

Review of this subsystem. Lots of good testing. Maybe some kind of overview 
documentation about the design. Maybe a diagram of how all these classes and interfaces
fit together? I've got end-to-end examples with memory working but I still wouldn't 
quite say I fully understand the arch. of the sub-system here.

### `./orchestration` (Complete?)

This was a pretty core piece and another direct port. I think we have pretty much
everything in here? Worth double checking. Needs good docs and tests.

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

**NOTE:** this module definitely needs some good tests. I could see some
subtle errors sneaking into the prompt tokenization/rendering code here.

### `./text` (TODO: nothing yet)

Ignored this module for now.

### `<root>` (Partial)

I have a working `Kernel` and a working `KernelBuilder`. The base interface
and custom exception are ported. I'm guessing the `Kernel` in particular
is missing some things, has some bugs, could be cleaner, etc. It's a big 
lump of code.

## Overall TODOs

We are currently missing a lot of the doc comments from C#. So a good review
of the code and a sweep for missing doc comments would be great.

We also are missing any _testing_. We should figure out how we want to test
(I think this project is auto-setup for `pytest`).

Finally, we are missing a lot of examples. It'd be great to have Python notebooks
that show off many of the features, many of the core skills, etc.

## Design Choices

I've tried to keep things as similar as possible to C#. There are two key 
differences:

1. I'm using `numpy` to store embeddings and do things like vector/matrix ops
2. I'm using `openai` to interface with (Azure) OpenAI 

There's also a lot of more subtle differences that come with moving to Python,
things like static properties, no method overloading, no extension methods, etc.
I've tried to still follow the C# version pretty directly, while compensating
for the difference in implementation language.

## Development

For now, I've been using `poetry` to manage Python dependencies and create
the original project scaffolding. This brings with it `pytest` for testing.
The `pyproject.toml` file is the main config file for `poetry`-based projects.

See the [Dev Setup](./DEV_SETUP.md) document for more details.

I've been using `black` to format files. This is nice as there's no choices
to argue over :) I've also been using `flake8` to lint the code. 

I have a basic `Makefile` that is setup to do `poetry install` and also 
use a tool called `pre-commit` to run linting/formatting on all the files.
Configuration for those things are in the `./conf/` directory.
