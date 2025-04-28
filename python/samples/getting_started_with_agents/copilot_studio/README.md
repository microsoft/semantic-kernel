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

If you **do not see Power Platform API**, follow [Step 2 in Power Platform API Authentication](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/enabling-power-platform-api-authentication) to add the API to your tenant.

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

> **Warning**: Service Principal login is **not generally supported** in the current version of the CopilotStudioClient.  
> **Important**: Your Copilot Studio Agent must support **User Anonymous authentication** for this flow to work.

### Steps

1. Open [Azure Portal](https://portal.azure.com)
2. Navigate to **Entra ID**
3. Go to **App registrations** → **New registration**
4. Fill out:
   - **Name**: Any name (e.g., `CopilotStudioServicePrincipal`)
   - **Supported account types**: `Accounts in this organization directory only`
5. Click **Register**

---

### Save the Following Values

From the **Overview** page of your registered app, note the following for later use:
- `Application (client) ID`
- `Directory (tenant) ID`

---

### Assign Required API Permissions

1. Go to: `Manage` → `API permissions`
2. Click **Add a permission**
3. Choose **APIs my organization uses**
4. Search for: **Power Platform API**

   *(If not listed, see the Tip below)*

5. Select:
   - **Application Permissions**
   - Expand `CopilotStudio`
   - Check `CopilotStudio.Copilots.Invoke`
6. Click **Add permissions**
7. *(Optional)* Click **Grant admin consent**

---

### Tip: Can't Find Power Platform API?

If you do **not** see **Power Platform API** in the list of available APIs:

Follow [Step 2 in the Power Platform API Authentication guide](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/enabling-power-platform-api-authentication) to register the Power Platform Admin API into your tenant manually.

---

### Configure Environment Variables

In your `.env` file or terminal environment, set the following:

```env
COPILOT_STUDIO_AGENT_APP_CLIENT_ID=<your-app-client-id>
COPILOT_STUDIO_AGENT_TENANT_ID=<your-tenant-id>
COPILOT_STUDIO_AGENT_ENVIRONMENT_ID=<your-env-id>
COPILOT_STUDIO_AGENT_AGENT_IDENTIFIER=<your-agent-id>
COPILOT_STUDIO_AGENT_CLIENT_SECRET=<your-client-secret>                  # Optional
COPILOT_STUDIO_AGENT_CLIENT_CERTIFICATE=<path-to-certificate.pem>       # Optional
COPILOT_STUDIO_AGENT_AUTH_MODE=service
```

