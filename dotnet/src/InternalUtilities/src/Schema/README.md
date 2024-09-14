The *.cs files in this folder, other than KernelJsonSchemaBuilder.cs, are a direct copy of the code at
https://github.com/eiriktsarpalis/stj-schema-mapper/tree/94b6d9b979f1a80a1c305605dfc6de3b7a6fe78b/src/JsonSchemaMapper.
They should be kept in sync with any changes made in that repo, and should be removed once the relevant replacements are available in System.Text.Json.

EXPOSE_JSON_SCHEMA_MAPPER should _not_ be defined so as to keep all of the functionality internal.

A .editorconfig is used to suppress code analysis violations this repo tries to enforce that the repo containing the copied code doesn't.