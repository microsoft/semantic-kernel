# Schema: Natural Language to SQL Console
Emulating other successful approaches (e.g.: [DIN](https://arxiv.org/abs/2304.11015)), injecting schema meta-data into the semantic prompt provides the structure that drives query generation.

Unlike other approaches, the prompts here are quite lean...relying almost entirely on schema expression and innate model capabilities.

## ⚙️ Schema Object Model
Pretty much what you'd expect.  Note: column type and primary key inclusion are captured, but not expressed in the YAML expression.  
> The [DIN approach](https://arxiv.org/abs/2304.11015) (et. al.) to the  [Spider challenge](https://yale-lily.github.io/spider) demonstrated type, nullity, etc... just aren't so impactful.  In the trade-off between vebosity and token usage, low/no-impact meta-data looses.

- [Schema](../../nl2sql.library/Schema/SchemaDefinition.cs)
- [Table](../../nl2sql.library/Schema/SchemaTable.cs)
- [Column](../../nl2sql.library/Schema/SchemaColumn.cs)

## ⚙️ Semantic Schema Format (YAML)
Examples of yaml formatted schema for inspection.  The actual semantic YAML is generated at runtime.

- [AdventureWorksLT.yaml](./AdventureWorksLT.yaml)
- [DescriptionTest.yaml](./DescriptionTest.yaml)

## ⚙️ Serialization Format (JSON)
These are the files that are deserialized at runtime.  The semantic YAML is generated at runtime.
> Note: This is where custom schema is written when using the [Reverse Engineering Harness](../../nl2sql.harness/SqlSchemaProviderHarness.cs).

- [AdventureWorksLT.json](./AdventureWorksLT.json)
- [DescriptionTest.json](./DescriptionTest.json)

## ⚙️ Objectives 
Seed objectives (...to get the ball rolling!).

- [AdventureWorksLT.objectives](./AdventureWorksLT.objectives)
- [DescriptionTest.objectives](./DescriptionTest.objectives)
