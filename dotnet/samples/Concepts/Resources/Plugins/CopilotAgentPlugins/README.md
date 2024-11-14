# Copilot Agent Plugins

## Generation

These plugins have been generated thanks to [kiota](https://aka.ms/kiota) and can be regenerated if needed.

```shell
cd dotnet/samples/Concepts/Resources/Plugins/CopilotAgentPlugins
```

### Calendar plugin

Microsoft Graph calendar events listing API for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/calendar/events#GET -o CopilotAgentPlugins/CalendarPlugin
```

### Contacts plugin

Microsoft Graph contacts listing API for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/contacts#GET -o CopilotAgentPlugins/ContactsPlugin
```

### DriveItem plugin

Microsoft Graph download a drive item for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /drive/root/children/{driveItem-id}/content#GET -o CopilotAgentPlugins/DriveItemPlugin
```

### Messages plugin

Microsoft Graph list message and create a draft message for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/messages#GET -i /me/messages#POST -o CopilotAgentPlugins/MessagesPlugin
```

### Astronomy plugin

NASA Astronomy Picture of the day endpoint mixed with Microsoft Graph messages to demonstrate a plugin with multiple APIs.

```shell
kiota plugin add -t APIPlugin -d ../OpenAPI/NASA/apod.yaml -i /apod#GET -o CopilotAgentPlugins/AstronomyPlugin
cp CopilotAgentPlugins/MessagesPlugin/messages-openapi.yml CopilotAgentPlugins/AstronomyPlugin
```

Add this snippet under runtimes

```json
{
    "type": "OpenApi",
    "auth": {
    "type": "None"
    },
    "spec": {
    "url": "messages-openapi.yml"
    },
    "run_for_functions": ["me_ListMessages"]
}
```

And this snippet under functions

```json
{
    "name": "me_ListMessages",
    "description": "Get an open extension (openTypeExtension object) identified by name or fully qualified name. The table in the Permissions section lists the resources that support open extensions. The following table lists the three scenarios where you can get an open extension from a supported resource instance."
}
```
