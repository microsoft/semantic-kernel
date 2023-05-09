// Copyright (c) Microsoft. All rights reserved.
import * as signalR from "@microsoft/signalr";

export class SKMultiUserChat {
    private hubConnection!: signalR.HubConnection;

    constructor(private readonly serviceUrl: string) {}

    // Set up a SignalR connection to the specified hub URL
    setupSignalRConnectionToChatHub() {
      const connectionHubUrl = (new URL('/chatHub', this.serviceUrl)).toString();

      const signalRConnectionOptions = {
        skipNegotiation: true,
        transport: signalR.HttpTransportType.WebSockets,
        logger: signalR.LogLevel.Warning
      };

      // Create the connection instance
      // withAutomaticReconnect will automatically try to reconnect and generate a new socket connection if needed
      this.hubConnection = new signalR.HubConnectionBuilder()
          .withUrl(connectionHubUrl, signalRConnectionOptions)
          .withAutomaticReconnect()
          .withHubProtocol(new signalR.JsonHubProtocol())
          .configureLogging(signalR.LogLevel.Information)
          .build();

      // Note: to keep the connection open the serverTimeout should be
      // larger than the KeepAlive value that is set on the server
      // keepAliveIntervalInMilliseconds default is 15000 and we are using default
      // serverTimeoutInMilliseconds default is 30000 and we are using 60000 set below
      this.hubConnection.serverTimeoutInMilliseconds = 60000;

      this.registerSignalReconnectionEvents();
      this.startSignalRConnection(this.hubConnection);
      this.registerSignalEvents();
    };

    startSignalRConnection = async (connection: { start: () => any; state: signalR.HubConnectionState; }) => {
      try {
        await connection.start();
        console.assert(connection.state === signalR.HubConnectionState.Connected);
        console.log('SignalR connection established');
      } catch (err) {
        console.assert(connection.state === signalR.HubConnectionState.Disconnected);
        console.error('SignalR Connection Error: ', err);
        setTimeout(() => this.startSignalRConnection(connection), 5000);
      }
    };

    registerSignalReconnectionEvents() {
      // Re-establish the connection if connection dropped
      this.hubConnection.onclose((error: any) => {
        console.assert(this.hubConnection.state === signalR.HubConnectionState.Disconnected);
        console.log('Connection closed due to error. Try refreshing this page to restart the connection', error);
      });

      this.hubConnection.onreconnecting((error: any) => {
        console.assert(this.hubConnection.state === signalR.HubConnectionState.Reconnecting);
        console.log('Connection lost due to error. Reconnecting.', error);
      });

      this.hubConnection.onreconnected((connectionId: any) => {
        console.assert(this.hubConnection.state === signalR.HubConnectionState.Connected);
        console.log('Connection reestablished. Connected with connectionId', connectionId);
      });
    }

    registerSignalEvents() {
      this.hubConnection.on("UserConnected", (connectionId: any) => {
        console.log(`User connected: ${connectionId}`);
      });

      // const receiveMessageFromBackend = (message: string) => {
      //   this.hubConnection.invoke("SendMessageToAllUsersExceptSelfAsync", "EventReceiveMessageFrontend", message);
      // //   this.hubConnection.invoke("SendMessageAsync", "UserA", "This is nonsense").catch(function (err) {
      // //     return console.error(err.toString());
      // // });
      // };
          
      this.hubConnection.on("ReceiveMessageFromBackend", this.EventReceiveMessageFromBackend);
      this.hubConnection.on("EventReceiveMessageFrontend", this.EventCallBackendFunctionThatInvokesTheFrontend);
    }

    EventReceiveMessageFromBackend = (message: string) => {
      console.log("Received message from backend: ", message);
    }

    EventReceiveMessageFrontend = (message: string) => {
      console.log("Received message back on frontend client: ", message);
    }

    EventCallBackendFunctionThatInvokesTheFrontend = (message: string) => {
      // message is passed along to the backend and then broadcasted to all the clients except the caller
      this.hubConnection.invoke("SendMessageToAllUsersExceptSelfAsync", "EventReceiveMessageFrontend", message);
    }
}