# Semantic Kernel - CopilotStudioAgent Quickstart

This README provides an overview on how to use the `CopilotStudioAgent` within Semantic Kernel. 
This agent allows you to interact with Microsoft Copilot Studio agents through programmatic APIs.

> ℹ️ **Note:** Knowledge sources must be configured **within** Microsoft Copilot Studio first. Streaming responses are **not currently supported**.

---

## 🔧 Prerequisites

2. Install `Microsoft.SemanticKernel.Agents.CopilotStudio` package:
     ```bash
     dotnet add package Microsoft.SemanticKernel.Agents.CopilotStudio --prerelease
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
