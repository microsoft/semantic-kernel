The *.cs files in this folder, other than KernelJsonSchemaBuilder.cs, are a direct copy of the code at
https://github.com/eiriktsarpalis/stj-schema-mapper/tree/b7d7f5a3794e48c45e2b5b0ab050d89aabfc94d6/src/JsonSchemaMapper.
They should be kept in sync with any changes made in that repo, and should be removed once the relevant replacements are available in System.Text.Json.

EXPOSE_JSON_SCHEMA_MAPPER should _not_ be defined so as to keep all of the functionality internal.

A .editorconfig is used to suppress code analysis violations this repo tries to enforce that the repo containing the copied code doesn't.