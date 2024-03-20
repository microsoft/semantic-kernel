This is a copy of the code at https://github.com/eiriktsarpalis/stj-schema-mapper/tree/main/src/JsonSchemaMapper. It should be kept in sync with any changes made in that repo.

Changes from that code:
- Public types changed to be internal and sealed
- Adding using namespaces due to global using not being employed
- Replaced use of collection expressions due to C# 12 not yet being used
- Removed use of primary constructors due to C# 12 not yet being used
- Removed ref readonly from parameter due to C# 12 not yet being used
- Used this. to map to style configuration
- Sort usings
- Remove trailing whitespace