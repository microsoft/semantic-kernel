# Semantic Kernel - CopilotStudioAgent Quickstart

This README provides an overview on how to use the [CopilotStudioAgent](../../../semantic_kernel/agents/copilot_studio/copilot_studio_agent.py) within Semantic Kernel. 
This agent allows you to interact with Microsoft Copilot Studio agents through programmatic APIs.

> ℹ️ **Note:** Knowledge sources must be configured **within** Microsoft Copilot Studio first. Streaming responses are **not currently supported**.

---

## 🔧 Prerequisites

1. Python 3.10+
2. Install Semantic Kernel with Copilot Studio dependencies:
   ```bash
   pip install semantic-kernel[copilot_studio]
   ```
3. An agent created in **Microsoft Copilot Studio**
4. Ability to create an application identity in Azure for a **Public Client/Native App Registration**, 
or access to an existing app registration with the `CopilotStudio.Copilots.Invoke` API permission assigned.

## Create a Copilot Agent in Copilot Studio

1. Go to [Microsoft Copilot Studio](https://copilotstudio.microsoft.com).
2. Create a new **Agent**.
3. Publish your newly created Agent.
4. In Copilot Studio, navigate to:  
   `Settings` → `Advanced` → `Metadata`

   Save the following values:
   - `Schema Name` (maps to `agent_identifier`)
   - `Environment ID`

## Create an Application Registration in Entra ID – User Interactive Login

> This step requires permissions to create application identities in your Azure tenant.

You will create a **Native Client Application Identity** (no client secret required).

1. Open [Azure Portal](https://portal.azure.com)
2. Navigate to **Entra ID**
3. Go to **App registrations** → **New registration**
4. Fill out:
   - **Name**: Any name you like
   - **Supported account types**: `Accounts in this organization directory only`
   - **Redirect URI**:  
     - Platform: `Public client/native (mobile & desktop)`
     - URI: `http://localhost`
5. Click **Register**
6. From the **Overview** page, note:
   - `Application (client) ID`
   - `Directory (tenant) ID`
7. Go to: `Manage` → `API permissions`
   - Click **Add permission**
   - Choose **APIs my organization uses**
   - Search for: **Power Platform API**

   If it's not listed, see **Tip** below.

8. Choose:
   - **Delegated Permissions**
   - Expand `CopilotStudio`
   - Select `CopilotStudio.Copilots.Invoke`
9. Click **Add permissions**
10. (Optional) Click **Grant admin consent**

### Tip

If you **do not see Power Platform API**, follow [Step 2 in Power Platform API Authentication](https://learn.microsoft.com/en-us/power-platform/admin/programmability-authentication-v2) to add the API to your tenant.

---

### Configure the Example Application - User Interactive Login

Once you've collected all required values:

1. Set the following environment variables in your terminal or .env file:

```env
COPILOT_STUDIO_AGENT_APP_CLIENT_ID=<your-app-client-id>
COPILOT_STUDIO_AGENT_TENANT_ID=<your-tenant-id>
COPILOT_STUDIO_AGENT_ENVIRONMENT_ID=<your-env-id>
COPILOT_STUDIO_AGENT_AGENT_IDENTIFIER=<your-agent-id>
COPILOT_STUDIO_AGENT_AUTH_MODE=interactive
```

## Create an Application Registration in Entra ID – Service Principal Login

> **Warning**: Service Principal login is **not yet supported** in the current version of the `CopilotStudioClient`.  

## Creating a `CopilotStudioAgent` Client

If all required environment variables are set correctly, you don't need to manually create or pass a `client`. Semantic Kernel will automatically construct the client using the environment configuration.

However, if you need to override any environment variables—such as when specifying custom credentials or cloud settings—you should create the `client` explicitly using `CopilotStudioAgent.create_client(...)` and then pass it to the agent constructor.

```python
client: CopilotClient = CopilotStudioAgent.create_client(
   auth_mode: CopilotStudioAgentAuthMode | Literal["interactive", "service"] | None = None,
   agent_identifier: str | None = None,
   app_client_id: str | None = None,
   client_secret: str | None = None,
   client_certificate: str | None = None,
   cloud: PowerPlatformCloud | None = None,
   copilot_agent_type: AgentType | None = None,
   custom_power_platform_cloud: str | None = None,
   env_file_encoding: str | None = None,
   env_file_path: str | None = None,
   environment_id: str | None = None,
   tenant_id: str | None = None,
   user_assertion: str | None = None,
)

agent = CopilotStudioAgent(
   client=client,
   name="<name>",
   instructions="<instructions>",
)
```