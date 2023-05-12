import * as signalR from "@microsoft/signalr";
import { AuthorRoles, IChatMessage } from './../../../libs/models/ChatMessage';

export interface UserAsk {
    input: string;
    variables: KeyValuePair<string, string>[];
}
  
export interface UserAskResult {
    value: string;
    variables?: KeyValuePair<string, string>[];
}
  
export interface KeyValuePair<K, V> {
    key: K;
    value: V;
}

const receiveMsgFromServerCallbackName = "ReceiveMessage" as string;

// Set up a SignalR connection to the messageRelayHub on the server
const setupSignalRConnectionToChatHub = () => {
    const connectionHubUrl = new URL("/messageRelayHub", process.env.REACT_APP_BACKEND_URI as string);
    const signalRConnectionOptions = {
        skipNegotiation: true,
        transport: signalR.HttpTransportType.WebSockets,
        logger: signalR.LogLevel.Warning
    };

    // Create the connection instance
    // withAutomaticReconnect will automatically try to reconnect and generate a new socket connection if needed
    var hubConnection = new signalR.HubConnectionBuilder()
        .withUrl(connectionHubUrl.toString(), signalRConnectionOptions)
        .withAutomaticReconnect()
        .withHubProtocol(new signalR.JsonHubProtocol())
        .configureLogging(signalR.LogLevel.Information)
        .build();

    // Note: to keep the connection open the serverTimeout should be
    // larger than the KeepAlive value that is set on the server
    // keepAliveIntervalInMilliseconds default is 15000 and we are using default
    // serverTimeoutInMilliseconds default is 30000 and we are using 60000 set below
    hubConnection.serverTimeoutInMilliseconds = 60000;
    return hubConnection;
};

const hubConnection = setupSignalRConnectionToChatHub();

const registerCommonSignalConnectionEvents = async () => {
    // Re-establish the connection if connection dropped
    hubConnection.onclose((error: any) => {
        console.assert(hubConnection.state === signalR.HubConnectionState.Disconnected);
        console.log('Connection closed due to error. Try refreshing this page to restart the connection', error);
    });

    hubConnection.onreconnecting((error: any) => {
        console.assert(hubConnection.state === signalR.HubConnectionState.Reconnecting);
        console.log('Connection lost due to error. Reconnecting.', error);
    });

    hubConnection.onreconnected((connectionId: any) => {
        console.assert(hubConnection.state === signalR.HubConnectionState.Connected);
        console.log('Connection reestablished. Connected with connectionId', connectionId);
    });

    hubConnection.on("UserConnected", (connectionId: any) => {
        console.debug(`User connected: ${connectionId}`);
    });
}

const onReceiveChatSkillAskResult = (store: any, userAskResult: UserAskResult) => {
    const message = {
        timestamp: new Date().getTime(),
        userName: 'bot',
        userId: 'bot',
        content: userAskResult.value,
        authorRole: AuthorRoles.Bot,
    } as IChatMessage;

    store.dispatch({ type: "conversations/updateConversationFromServer", payload: { message } });
}

export const startSignalRConnection = async () => {
    try {
        registerCommonSignalConnectionEvents();
        await hubConnection.start();
        console.assert(hubConnection.state === signalR.HubConnectionState.Connected);
        console.log('SignalR connection established');
    } catch (err) {
        console.assert(hubConnection.state === signalR.HubConnectionState.Disconnected);
        console.error('SignalR Connection Error: ', err);
        setTimeout(() => startSignalRConnection(), 5000);
    }
};

export const signalRMiddleware = (store: any) => {
    return (next: any) => async (action: any) => {
        switch (action.type) {
            case "conversations/updateConversationFromUser":
                await hubConnection.invoke("SendMessageAsync", getSelectedChatID(store), action.payload.message).catch(
                    err => console.error(err.toString())
                );
                break;
            case "conversations/setConversations":
                Object.keys(action.payload).map(async (id) => {
                    await hubConnection.invoke("AddClientToGroupAsync", id).catch(
                        err => console.error(err.toString())
                    );
                });
                break;
            case "conversations/addConversation":
                await hubConnection.invoke("AddClientToGroupAsync", action.payload.id).catch(
                    err => console.error(err.toString())
                );
                break;
        }

        return next(action);
    }
};

export const signalRRegisterEvents = async (store: any) => {
    hubConnection.on(receiveMsgFromServerCallbackName, (message: UserAsk, chatId: string) => {
        store.dispatch({ type: "conversations/updateConversationFromServer", payload: { message, chatId } });
    });

    hubConnection.on("receiveChatSkillAskResult", (userAskResult: UserAskResult) => {
        onReceiveChatSkillAskResult(store, userAskResult);
    });
};

const getSelectedChatID = (store: any) => {
    return store.getState().conversations.selectedId;
};
