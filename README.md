💬 Chat App – Real-Time Messaging Using Python & MySQL
This is a simple yet functional console-based chat application built with Python and MySQL, designed for learning, experimentation, and small-scale use over a network. The app allows two or more users to communicate in real time after signing up or logging in — all data is managed using a MySQL backend.

🧠 Why I Built This
I wanted to understand how real-time communication works behind the scenes. Instead of using external APIs or frameworks, I built everything from scratch using Python’s socket and threading modules, combined with MySQL for storing user credentials, messages, and conversation history.

🛠️ Features
👥 Login/Signup System with hashed passwords

🧾 Stores messages and user data in MySQL

📡 Real-time messaging using Python sockets

🚪 Graceful exit handling (notifies when users leave)

🧵 Multithreading for concurrent message send/receive

💻 Works across devices on the same network (LAN)

⚙️ Technologies Used
Python 3

MySQL (via mysql-connector-python)

Socket (for real-time communication)

Threading (to handle simultaneous input/output)

📦 How It Works
Start the Server
Runs on a specified host/port and handles all message routing.

Run the Client App
Connect to the server, choose to login or sign up.

Start Chatting
Send and receive messages instantly with another user on the network.
