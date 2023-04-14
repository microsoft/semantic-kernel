# Feature matrix Python and C\#

The Python codebase has a bulk of the Semantic Kernel architecture re-implemented, but
is not yet fully complete. Major things like `tests` and `docs` are work in progress.

This is a high-level overview of where things stand towards reaching feature
parity with the C# reference implementation.

|                                     |        |                                                                                 |
|-------------------------------------|--------|---------------------------------------------------------------------------------|
|                                     | Python | Notes                                                                           |
| `./ai/embeddings`                   | 🔄     | Using Numpy for embedding representation. Vector operations not yet implemented |
| `./ai/openai`                       | 🔄     | Makes use of the OpenAI Python package. AzureOpenAI* not implemented            |
| `./configuration`                   | ✅     | Direct port. Check inline docs                                                  |
| `./core_skills`                     | 🔄     | `TextMemorySkill` implemented. Others not                                       |
| `./diagnostics`                     | ✅     | Direct port of custom exceptions and validation helpers                         |
| `./kernel_extensions`               | 🔄     | Extensions take kernel as first argument and are exposed via `sk.extensions.*`  |
| `./memory`                          | 🔄     | Can simplify by relying on Numpy NDArray                                        |
| `./planning`                        | ❌     | Not yet implemented                                                             |
| `./semantic_functions/partitioning` | ❌     | Not yet implemented                                                             |

## Design Choices

The overall architecture of the core kernel is consistent across Python and C#,
however, the code should follow common paradigms and style of each language.

During the initial development phase, many Python best practices have been ignored
in the interest of velocity and feature parity. The project is now going through
a refactoring exercise to increase code quality.

To make the Kernel as lightweight as possible, the core pip package should have
a minimal set of external dependencies. On the other hand, the SDK should not
reinvent mature solutions already available, unless of major concerns.
