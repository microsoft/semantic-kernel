// Copyright (c) Microsoft. All rights reserved.
import * as signalR from "@microsoft/signalr";

export class SKMultiUserChat {
    constructor(private readonly serviceUrl: string) {}

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

    // Set up a SignalR connection to the specified hub URL, and actionEventMap.
    // actionEventMap should be an object mapping event names, to eventHandlers that will
    // be dispatched with the message body.
    setupSignalRConnectionToChatHub() {
      const connectionHubUrl = (new URL('/chatHub', this.serviceUrl)).toString();

      const signalRConnectionOptions = {
        skipNegotiation: true,
        transport: signalR.HttpTransportType.WebSockets,
        logger: signalR.LogLevel.Warning
      };

      // Create the connection instance
      // withAutomaticReconnect will automatically try to reconnect and generate a new socket connection if needed
      var connection = new signalR.HubConnectionBuilder()
          .withUrl(connectionHubUrl, signalRConnectionOptions)
          .withAutomaticReconnect()
          .withHubProtocol(new signalR.JsonHubProtocol())
          .configureLogging(signalR.LogLevel.Information)
          .build();

      // Note: to keep the connection open the serverTimeout should be
      // larger than the KeepAlive value that is set on the server
      // keepAliveIntervalInMilliseconds default is 15000 and we are using default
      // serverTimeoutInMilliseconds default is 30000 and we are using 60000 set below
      connection.serverTimeoutInMilliseconds = 60000;

      // Re-establish the connection if connection dropped
      connection.onclose((error: any) => {
        console.assert(connection.state === signalR.HubConnectionState.Disconnected);
        console.log('Connection closed due to error. Try refreshing this page to restart the connection', error);
      });

      connection.onreconnecting((error: any) => {
        console.assert(connection.state === signalR.HubConnectionState.Reconnecting);
        console.log('Connection lost due to error. Reconnecting.', error);
      });

      connection.onreconnected((connectionId: any) => {
        console.assert(connection.state === signalR.HubConnectionState.Connected);
        console.log('Connection reestablished. Connected with connectionId', connectionId);
      });
      
      this.startSignalRConnection(connection);

      // connection.on('OnEvent', (res: { eventType: string | number; }) => {
      //   const eventHandler = actionEventMap[res.eventType];
      //   eventHandler && dispatch(eventHandler(res));
      // });

      return connection;
    };

    MessageEventReaction() : void {
      //Do nothing
    }

    SendTestMessage = () => {      
      var connection = this.setupSignalRConnectionToChatHub();
      
      connection.on("UserConnected", (connectionId) => {
        console.log(`User connected: ${connectionId}`);
      });

      const receiveMessage = (message: string) => {
        console.log("Received message from client: ", message);
        // Send a message back to the client
        connection.invoke("Func2Async", "user", "Hello, client!");
        connection.invoke("SendMessageAsync", "UserA", "This is nonsense").catch(function (err) {
          return console.error(err.toString());
      });
      };
          
      connection.on("ReceiveMessage", receiveMessage);
    }
}