import React, { useEffect, useState } from "react";
import * as signalR from "@microsoft/signalr";

const ChatApp: React.FC = () => {
  const [connection, setConnection] = useState<signalR.HubConnection | null>(null);
  const [conversationId, setConversationId] = useState<string>("userId");
  const [messages, setMessages] = useState<{ userId: string; content: string }[]>([]);
  const [userMessage, setUserMessage] = useState<string>("");

  // Establish SignalR connection
  useEffect(() => {

    const newConnection = new signalR.HubConnectionBuilder()
      .withUrl("https://localhost:58844/chatHub", {withCredentials: true}/*{
        accessTokenFactory: () => "your-auth-token-here", // Replace with actual token retrieval
      }*/)
      .withAutomaticReconnect()
      .build();

    newConnection
      .start()
      .then(() => {
        console.log("Connected to the SignalR hub.");
        setConnection(newConnection);
      })
      .catch((err) => console.error("Connection failed:", err));

    return () => {
      newConnection.stop();
    };
  }, []);

  // Handle incoming messages and events
  useEffect(() => {
    if (connection) {
      connection.on("ReceiveMessage", (userId: string, content: string) => {
        console.log(`received message: ${userId} - ${content}`)
        setMessages((prevMessages) => [...prevMessages, { userId, content }]);
      });

      connection.on("ConversationHistory", (history: { senderId: string; content: string }[]) => {
        const formattedMessages = history.map((msg) => ({ userId: msg.senderId, content: msg.content }));
        setMessages(formattedMessages);
      });

      connection.on("ConversationReset", () => {
        setMessages([]);
        console.log(`Conversation ${conversationId} reset.`);
      });
    }
  }, [connection, conversationId]);

  // Join a conversation
  const joinConversation = async () => {
    if (connection) {
      try {
        await connection.invoke("JoinConversationAsync", conversationId);
        console.log(`Joined conversation ${conversationId}`);
      } catch (err) {
        console.error("Error joining conversation:", err);
      }
    }
  };

  // Send a message
  const sendMessage = async () => {
    if (connection) {
      try {
        await connection.invoke("SendUserMessageAsync", conversationId, userMessage);
        console.log(`Message sent: ${userMessage}`);
        setUserMessage(""); // Clear input field
      } catch (err) {
        console.error("Error sending message:", err);
      }
    }
  };

  // Reset the conversation
  const resetConversation = async () => {
    if (connection) {
      try {
        await connection.invoke("ResetConversationAsync", conversationId);
        console.log(`Conversation ${conversationId} reset.`);
      } catch (err) {
        console.error("Error resetting conversation:", err);
      }
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>React + TypeScript Chat App</h1>
      <div
        id="chat-window"
        style={{ border: "1px solid black", height: "300px", overflowY: "scroll", marginBottom: "10px", padding: "10px" }}
      >
        {messages.map((msg, index) => (
          <div key={index}>
            <strong>{msg.userId}:</strong> {msg.content}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={userMessage}
        onChange={(e) => setUserMessage(e.target.value)}
        placeholder="Type your message"
        style={{ width: "80%", marginRight: "10px" }}
      />
      <button onClick={sendMessage} style={{ marginRight: "10px" }}>
        Send
      </button>
      <button onClick={joinConversation} style={{ marginRight: "10px" }}>
        Join Conversation
      </button>
      <button onClick={resetConversation}>Reset Conversation</button>
    </div>
  );
};

export default ChatApp;
