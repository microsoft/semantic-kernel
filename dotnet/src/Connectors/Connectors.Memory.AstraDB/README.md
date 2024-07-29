# Microsoft.SemanticKernel.Connectors.AstraDB

This connector uses [Astra DB](https://astra.datastax.com) to implement Semantic Memory.

## Quick Start

1. **Create an Astra DB Account:**
   - Sign up at [Astra DB](https://astra.datastax.com).
   - Log in to the dashboard.

2. **Create a Database:**
   - Create a database from dashboard.

3. **Generate an Application Token:**
   - Generate Application Token[https://docs.datastax.com/en/astra-db-serverless/administration/manage-application-tokens.html] with accurate permissions.
   - Navigate your API Endpoint.

4. **Configure the Connection:**
   - Add configuration values to `appsettings.json`:
     ```json
     {
         "AstraDB": {
             "ApiEndpoint": "https://<your_db_id>-<your_region>.apps.astra.datastax.com",
             "AppToken": "your_app_token",
             "KeySpace": "your_keyspace_name",
             "VectorSize": "128"
         }
     }

5. **Initialize AstraDBMemoryStore:**
   ```csharp
   var astraDBMemoryStore = new AstraDBMemoryStore(
       "https://<your_db_id>-<your_region>.apps.astra.datastax.com",
       "your_app_token",
       "your_keyspace_name",
       128
   );
   ````