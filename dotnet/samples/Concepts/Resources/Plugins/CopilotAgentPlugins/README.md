# Copilot Agent Plugins

## Generation

These plugins have been generated thanks to [kiota](https://aka.ms/kiota) and can be regenerated if needed.

```shell
cd dotnet/samples/Concepts/Resources/Plugins
```

### Calendar plugin

Microsoft Graph calendar events listing API for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/calendar/events#GET -o CopilotAgentPlugins/CalendarPlugin --pn Calendar
```

### Contacts plugin

Microsoft Graph contacts listing API for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/contacts#GET -o CopilotAgentPlugins/ContactsPlugin --pn Contacts
```

### DriveItem plugin

Microsoft Graph download a drive item for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /drives/{drive-id}/items/{driveItem-id}/content#GET -o CopilotAgentPlugins/DriveItemPlugin --pn DriveItem
```

### Messages plugin

Microsoft Graph list message and create a draft message for the current user.

```shell
kiota plugin add -t APIPlugin -d https://aka.ms/graph/v1.0/openapi.yaml -i /me/messages#GET -i /me/sendMail#POST -o CopilotAgentPlugins/MessagesPlugin --pn Messages
```

### Astronomy plugin

NASA Astronomy Picture of the day endpoint mixed with Microsoft Graph messages to demonstrate a plugin with multiple APIs.

```shell
kiota plugin add -t APIPlugin -d ./OpenAPI/NASA/apod.yaml -i /apod#GET -o CopilotAgentPlugins/AstronomyPlugin --pn Astronomy
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
    "description": "Get the messages in the signed-in user\u0026apos;s mailbox (including the Deleted Items and Clutter folders). Depending on the page size and mailbox data, getting messages from a mailbox can incur multiple requests. The default page size is 10 messages. Use $top to customize the page size, within the range of 1 and 1000. To improve the operation response time, use $select to specify the exact properties you need; see example 1 below. Fine-tune the values for $select and $top, especially when you must use a larger page size, as returning a page with hundreds of messages each with a full response payload may trigger the gateway timeout (HTTP 504). To get the next page of messages, simply apply the entire URL returned in @odata.nextLink to the next get-messages request. This URL includes any query parameters you may have specified in the initial request. Do not try to extract the $skip value from the @odata.nextLink URL to manipulate responses. This API uses the $skip value to keep count of all the items it has gone through in the user\u0026apos;s mailbox to return a page of message-type items. It\u0026apos;s therefore possible that even in the initial response, the $skip value is larger than the page size. For more information, see Paging Microsoft Graph data in your app. Currently, this operation returns message bodies in only HTML format. There are two scenarios where an app can get messages in another user\u0026apos;s mail folder:"
}
```
