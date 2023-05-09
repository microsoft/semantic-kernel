// Copyright (c) Microsoft. All rights reserved.
import * as signalR from "@microsoft/signalr";

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

      this.registerCommonSignalReconnectionEvents();
      this.startSignalRConnection(this.hubConnection);

      return this.hubConnection;
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

    registerCommonSignalReconnectionEvents() {
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

      this.hubConnection.on("UserConnected", (connectionId: any) => {
        console.log(`User connected: ${connectionId}`);
      });
    }
}