import * as signalR from "@microsoft/signalr";

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

export const signalRMiddleware = (store: any) => {
    return (next: any) => async (action: any) => {
        console.log("signalRMiddleware action", action);
        console.log("signalRMiddleware store", store);

        if (action.type === "conversations/updateConversationFromUser") {
            await connection.invoke("SendMessage", action.payload.message);
        }

        return next(action);
    }
}

export const signalRStart = async (store: any) => {
    connection.on("ReceiveMessage", (message: any) => {
        store.dispatch({ type: "conversations/updateConversationFromServer", payload: { message } });
        console.log("ReceiveMessage", message);
    });

    await connection.start().catch(err => console.error(err.toString()));
}