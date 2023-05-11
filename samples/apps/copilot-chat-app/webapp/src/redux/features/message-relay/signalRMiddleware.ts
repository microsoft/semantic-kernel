import * as signalR from "@microsoft/signalr";
import { AuthorRoles } from './../../../libs/models/ChatMessage';
import { IChatMessage } from './../../../libs/models/ChatMessage';

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

const url = new URL("/messageRelayHub", process.env.REACT_APP_BACKEND_URI as string);
const signalRConnectionOptions = {
    skipNegotiation: true,
    transport: signalR.HttpTransportType.WebSockets,
    logger: signalR.LogLevel.Warning
};
const connection = new signalR.HubConnectionBuilder()
    .withUrl(url.toString(), signalRConnectionOptions)
    .withAutomaticReconnect()
    .withHubProtocol(new signalR.JsonHubProtocol())
    .configureLogging(signalR.LogLevel.Information)
    .build();

const respondToServerCallbackName = "ReceiveMessageFromServer" as string;

export const signalRMiddleware = (store: any) => {
    return (next: any) => async (action: any) => {
        console.log("signalRMiddleware action", action);
        console.log("signalRMiddleware store", store);

        if (action.type === "conversations/updateConversationFromUser") {
            await connection.invoke("SendMessageToAllUsersExceptSelfAsync", respondToServerCallbackName, action.payload.message);
        }

        return next(action);
    }
}

export const signalRStart = async () => {
    await connection.start().catch(err => console.error(err.toString()));
}

export const signalRRegisterEvents = async (store: any) => {
    connection.on(respondToServerCallbackName, (message: UserAsk) => {
        store.dispatch({ type: "conversations/updateConversationFromServer", payload: { message } });
        console.log("ReceiveMessage", message);
    });

    connection.on("receiveChatSkillAskResult", (message: UserAskResult) => {
        const messageResult = {
            timestamp: new Date().getTime(),
            userName: 'bot',
            userId: 'bot',
            content: message.value,
            authorRole: AuthorRoles.Bot,
        } as IChatMessage;

        store.dispatch({ type: "conversations/updateConversationFromServer", payload: { messageResult } });
        console.log("ReceiveMessage", message);
    });
}
