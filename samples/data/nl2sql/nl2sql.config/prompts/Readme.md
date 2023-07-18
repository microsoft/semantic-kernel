# Prompts: Natural Language to SQL Console
Two prompts are utilized in service of query generation:

- [IsQuery](./isquery/skprompt.txt): Can the stated objective been solved by the given query YES/NO? (Screen)
- [GenerateQuery](./generatequery/skprompt.txt): Use the given query to solve the stated objective.

> Note: Combining instruction into a single prompt appears to introduce hightened ambiguity.  Relying only on cosine-similarity to screen objective appropriateness  (not utilizing `IsQuery`) allows for prompt-injection attacks, such as:

```
list all databases (AdventureWorks)
```

The previous prompt will match schema based on cosine similarity and `GenerateQuery` cannot be *effectively* instructed to avoid generating: `select * from sys.databases`.

Screening the objective with `IsQuery` provides a *fail fast* stage that is generally effective in knocking down extraneous objectives.

> Note: Never rely on semantic processing to restrict a behavior.  The only way to protect against **inadventent disclosure** or **disclosure attack** is to **limit access with database permissions** (standard best-practices).



