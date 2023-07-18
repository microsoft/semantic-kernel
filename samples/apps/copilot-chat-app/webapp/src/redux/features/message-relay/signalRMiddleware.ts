// Copyright (c) Microsoft. All rights reserved.

import * as signalR from '@microsoft/signalr';
import { AnyAction, Dispatch } from '@reduxjs/toolkit';
import { AlertType } from '../../../libs/models/AlertType';
import { IChatUser } from '../../../libs/models/ChatUser';
import { PlanState } from '../../../libs/models/Plan';
import { IAskResult } from '../../../libs/semantic-kernel/model/AskResult';
import { addAlert } from '../app/appSlice';
import { ChatState } from '../conversations/ChatState';
import { AuthorRoles, ChatMessageType, IChatMessage } from './../../../libs/models/ChatMessage';
import { Store, StoreMiddlewareAPI, getSelectedChatID } from './../../app/store';

// These have to match the callback names used in the backend
const enum SignalRCallbackMethods {
    ReceiveMessage = 'ReceiveMessage',
    ReceiveResponse = 'ReceiveResponse',
    UserJoined = 'UserJoined',
    ReceiveUserTypingState = 'ReceiveUserTypingState',
    ReceiveBotResponseStatus = 'ReceiveBotResponseStatus',
    GlobalDocumentUploaded = 'GlobalDocumentUploaded',
    ChatDocumentUploaded = 'ChatDocumentUploaded',
    ChatEdited = 'ChatEdited',
}

// The action sent to the SignalR middleware.
interface SignalRAction extends AnyAction {
    payload: {
        message?: IChatMessage;
        userId?: string;
        isTyping?: boolean;
        id?: string;
    };
}

// Set up a SignalR connection to the messageRelayHub on the server
const setupSignalRConnectionToChatHub = () => {
    const connectionHubUrl = new URL('/messageRelayHub', process.env.REACT_APP_BACKEND_URI);
    const signalRConnectionOptions = {
        skipNegotiation: true,
        transport: signalR.HttpTransportType.WebSockets,
        logger: signalR.LogLevel.Warning,
    };

    // Create the connection instance
    // withAutomaticReconnect will automatically try to reconnect and generate a new socket connection if needed
    const hubConnection = new signalR.HubConnectionBuilder()
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

const registerCommonSignalConnectionEvents = (store: Store) => {
    // Re-establish the connection if connection dropped
    hubConnection.onclose((error) => {
        if (hubConnection.state === signalR.HubConnectionState.Disconnected) {
            const errorMessage = 'Connection closed due to error. Try refreshing this page to restart the connection';
            store.dispatch(addAlert({ message: String(errorMessage), type: AlertType.Error }));
            console.log(errorMessage, error);
        }
    });

    hubConnection.onreconnecting((error) => {
        if (hubConnection.state === signalR.HubConnectionState.Reconnecting) {
            const errorMessage = 'Connection lost due to error. Reconnecting...';
            store.dispatch(addAlert({ message: String(errorMessage), type: AlertType.Info }));
            console.log(errorMessage, error);
        }
    });

    hubConnection.onreconnected((connectionId = '') => {
        if (hubConnection.state === signalR.HubConnectionState.Connected) {
            const message = 'Connection reestablished.';
            store.dispatch(addAlert({ message, type: AlertType.Success }));
            console.log(message + ` Connected with connectionId ${connectionId}`);
        }
    });
};

export const startSignalRConnection = (store: Store) => {
    registerCommonSignalConnectionEvents(store);
    hubConnection
        .start()
        .then(() => {
            console.assert(hubConnection.state === signalR.HubConnectionState.Connected);
            console.log('SignalR connection established');
        })
        .catch((err) => {
            console.assert(hubConnection.state === signalR.HubConnectionState.Disconnected);
            console.error('SignalR Connection Error: ', err);
            setTimeout(() => {
                startSignalRConnection(store);
            }, 5000);
        });
};
export const signalRMiddleware = (store: StoreMiddlewareAPI) => {
    return (next: Dispatch) => (action: SignalRAction) => {
        // Call the next dispatch method in the middleware chain before performing any async logic
        const result = next(action);

        // The following actions will be captured by the SignalR middleware and broadcasted to all clients.
        switch (action.type) {
            case 'conversations/updateConversationFromUser':
                hubConnection
                    .invoke('SendMessageAsync', getSelectedChatID(), action.payload.message)
                    .catch((err) => store.dispatch(addAlert({ message: String(err), type: AlertType.Error })));
                break;
            case 'conversations/updateUserIsTyping':
                hubConnection
                    .invoke(
                        'SendUserTypingStateAsync',
                        getSelectedChatID(),
                        action.payload.userId,
                        action.payload.isTyping,
                    )
                    .catch((err) => store.dispatch(addAlert({ message: String(err), type: AlertType.Error })));
                break;
            case 'conversations/setConversations':
                Promise.all(
                    Object.keys(action.payload).map(async (id) => {
                        await hubConnection.invoke('AddClientToGroupAsync', id);
                    }),
                ).catch((err) => store.dispatch(addAlert({ message: String(err), type: AlertType.Error })));
                break;
            case 'conversations/addConversation':
                hubConnection
                    .invoke('AddClientToGroupAsync', action.payload.id)
                    .catch((err) => store.dispatch(addAlert({ message: String(err), type: AlertType.Error })));
                break;
        }

        return result;
    };
};

export const registerSignalREvents = (store: Store) => {
    hubConnection.on(SignalRCallbackMethods.ReceiveMessage, (message: IChatMessage, chatId: string) => {
        store.dispatch({ type: 'conversations/updateConversationFromServer', payload: { message, chatId } });
    });

    hubConnection.on(SignalRCallbackMethods.ReceiveResponse, (askResult: IAskResult, chatId: string) => {
        const loggedInUserId = store.getState().app.activeUserInfo?.id;
        const originalMessageUserId: string | undefined = askResult.variables.find((v) => v.key === 'userId')?.value;
        const responseToLoggedInUser = loggedInUserId === originalMessageUserId;
        const messageType = Number(askResult.variables.find((v) => v.key === 'messageType')?.value) as ChatMessageType;
        const promptTokenUsage = askResult.variables.find((v) => v.key === 'promptTokenUsage')?.value;
        const dependencyTokenUsage = askResult.variables.find((v) => v.key === 'dependencyTokenUsage')?.value;

        const message = {
            type: messageType,
            timestamp: new Date().getTime(),
            userName: 'bot',
            userId: 'bot',
            content: askResult.value,
            prompt: askResult.variables.find((v) => v.key === 'prompt')?.value,
            authorRole: AuthorRoles.Bot,
            id: askResult.variables.find((v) => v.key === 'messageId')?.value,
            state:
                messageType === ChatMessageType.Plan && responseToLoggedInUser
                    ? PlanState.PlanApprovalRequired
                    : PlanState.Disabled,
            tokenUsage: {
                prompt: responseToLoggedInUser ? (promptTokenUsage ? parseInt(promptTokenUsage) : 0) : undefined,
                dependency: responseToLoggedInUser
                    ? dependencyTokenUsage
                        ? parseInt(dependencyTokenUsage)
                        : 0
                    : undefined,
            },
        } as IChatMessage;

        store.dispatch({ type: 'conversations/updateConversationFromServer', payload: { message, chatId } });
    });

    hubConnection.on(SignalRCallbackMethods.UserJoined, (chatId: string, userId: string) => {
        const user: IChatUser = {
            id: userId,
            online: false,
            fullName: '',
            emailAddress: '',
            isTyping: false,
            photo: '',
        };
        store.dispatch({ type: 'conversations/addUserToConversation', payload: { user, chatId } });
    });

    hubConnection.on(
        SignalRCallbackMethods.ReceiveUserTypingState,
        (chatId: string, userId: string, isTyping: boolean) => {
            store.dispatch({
                type: 'conversations/updateUserIsTypingFromServer',
                payload: { chatId, userId, isTyping },
            });
        },
    );

    hubConnection.on(SignalRCallbackMethods.ReceiveBotResponseStatus, (chatId: string, status: string) => {
        store.dispatch({ type: 'conversations/updateBotResponseStatusFromServer', payload: { chatId, status } });
    });

    hubConnection.on(SignalRCallbackMethods.GlobalDocumentUploaded, (fileNames: string, userName: string) => {
        store.dispatch(addAlert({ message: `${userName} uploaded ${fileNames} to all chats`, type: AlertType.Info }));
    });

    hubConnection.on(SignalRCallbackMethods.ChatDocumentUploaded, (message: IChatMessage, chatId: string) => {
        store.dispatch({ type: 'conversations/updateConversationFromServer', payload: { message, chatId } });
    });

    hubConnection.on(SignalRCallbackMethods.ChatEdited, (chat: ChatState) => {
        const { id, title } = chat;
        if (!(id in store.getState().conversations.conversations)) {
            store.dispatch(
                addAlert({
                    message: `Chat ${id} not found in store. Chat edited signal from server is not processed.`,
                    type: AlertType.Error,
                }),
            );
        }
        store.dispatch({ type: 'conversations/editConversationTitle', payload: { id, newTitle: title } });
    });
};
