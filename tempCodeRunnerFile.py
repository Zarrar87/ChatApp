import mysql.connector as sq
import time
import threading
import hashlib
import queue


db = sq.connect(
    host = 'localhost',
    user = 'root',
    password = '1234'
)

mycursor = db.cursor(buffered=True)

mycursor.execute("CREATE DATABASE IF NOT EXISTS chatapp")
mycursor.execute("USE chatapp")

try:
    mycursor.execute("ALTER TABLE users ADD COLUMN password VARCHAR(255)")
except sq.errors.ProgrammingError:
    pass  # Probably means column already exists
except sq.Error as e:
    if "Duplicate column name" in str(e):
        pass  # Ignore if column already added
    else:
        raise  # Show error if it's something else


mycursor.execute("""
CREATE TABLE IF NOT EXISTS users
        (
        id int auto_increment primary key,
        name varchar(50),
        email varchar(50) Unique
        )
""")

mycursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    last_message TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
""")

mycursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT,
    sender_id INT,
    receiver_id INT,
    content MEDIUMTEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
)
""")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def view_all_conversations():
    mycursor.execute("""
        SELECT c.id, u1.name, u1.email, u2.name, u2.email, c.last_message, c.last_updated
        FROM conversations c
        JOIN users u1 ON c.user1_id = u1.id
        JOIN users u2 ON c.user2_id = u2.id
    """)
    all_convos = mycursor.fetchall()

    print("\nAll Conversations:\n")
    for convo in all_convos:
        print(f"ID: {convo[0]} | {convo[1]} ({convo[2]}) ↔ {convo[3]} ({convo[4]})")
        print(f"Last Message: {convo[5]} | Updated: {convo[6]}\n")

    convo_id = input("Enter conversation ID to view messages: ")
    mycursor.execute("""
        SELECT u.name, m.content, m.sent_at FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.conversation_id = %s ORDER BY m.sent_at
    """, (convo_id,))
    messages = mycursor.fetchall()

    print("\nChat History:\n")
    for msg in messages:
        print(f"{msg[0]}: {msg[1]} ({msg[2]})")


def user_signin():
    user_name = input("Enter Your Name: ")
    while True:
        user_email = input("Email: ")
        if "@" in user_email and "." in user_email:
            break
        else:
            print("Enter valid email")

    password = input("Password: ")
    hashed_pw = hash_password(password)

    try:
        mycursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (user_name, user_email, hashed_pw))
        db.commit()
        print("Signup successful!")
    except sq.IntegrityError:
        print("A user with that email already exists.")


def user_login():
    while True:
        email = input("Enter Email: ")
        if "@" in email and "." in email:
            break
        else:
            print("Enter valid email")

    password = input("Enter Password: ")
    hashed_pw = hash_password(password)

    mycursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashed_pw))
    query = mycursor.fetchone()

    if query:
        print(f"Login successful! Welcome back, {query[1]}")
        return query
    else:
        print("Invalid email or password.")
        return None


def get_or_create_conversation(user1_id, user2_id):
    #This function checks if the conversation between two users already exists
    #it Works both ways
    mycursor.execute("""
        SELECT * FROM conversations 
        WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
    """, (user1_id, user2_id, user2_id, user1_id))
    convo = mycursor.fetchone()

    #if conversation exists then it will return there first conversation
    if convo:
        return convo[0]
    else:

        mycursor.execute("""
            INSERT INTO conversations (user1_id, user2_id) VALUES (%s, %s)
        """, (user1_id, user2_id))
        db.commit()
        #this will return the latest converstarion
        return mycursor.lastrowid
    
def send_message(convo_id, sender_id, receiver_id, content):   
#this query will add new converstion to the database MESSAGES
    mycursor.execute("""
        INSERT INTO messages (conversation_id, sender_id, receiver_id, content)
        VALUES (%s, %s, %s, %s)
    """, (convo_id, sender_id, receiver_id, content))
    #this query will update the already existion converstion in CONVERSATION table
    mycursor.execute("""
        UPDATE conversations SET last_message = %s WHERE id = %s
    """, (content, convo_id))
    db.commit()


"""
This function takes 2 arguments
1. conversation ID
2. Last_conversation ID
This function will select messages after 2nd id Messages (Meanin latest messages)
"""
def fetch_messages(convo_id, last_id):
    mycursor.execute("""
        SELECT id, sender_id, content, sent_at FROM messages 
        WHERE conversation_id = %s AND id > %s ORDER BY id ASC
    """, (convo_id, last_id))
    return mycursor.fetchall()

#To continuesly check latest messages
"""
msg[0] = id (used to track last message)
msg[1] = sender_id (sender)
msg[2] = content
msg[3] = send_at (tine)
"""
message_queue = queue.Queue()
def background_receive(convo_id, self_id):
    last_id = 0
    while True:
        msgs = fetch_messages(convo_id, last_id)
        for msg in msgs:
            last_id = msg[0]
            if msg[1] != self_id:
                message_queue.put(f"\nFriend: {msg[2]} ({msg[3]})")
        time.sleep(1)


def ensure_admin_user():
    admin_email = "admin@chat.com"
    admin_name = "Admin"
    admin_password = hash_password("admin123")

    mycursor.execute("SELECT * FROM users WHERE email = %s", (admin_email,))
    admin_exists = mycursor.fetchone()

    if not admin_exists:
        mycursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (admin_name, admin_email, admin_password)
        )
        db.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")

def main():
    ensure_admin_user()
    try:
        print("1. Sign Up\n2. Login")
        choice = input("Choice: ")
        if choice == "1":
            user_signin()
            user = user_login()
        else:
            user = user_login()

        if not user:
            return

        my_id = user[0]
        email = user[2]  
        name = user[1]

        if email == "admin@chat.com":
            view_all_conversations()
            input("Press Enter to exit...")
            return

        # Regular user chat flow
        friend_email = input("Enter email of user to chat with: ")
        mycursor.execute("SELECT * FROM users WHERE email = %s", (friend_email,))
        friend = mycursor.fetchone()

        if not friend:
            print("No such user.")
            input("Press Enter to exit...")
            return

        friend_id = friend[0]
        convo_id = get_or_create_conversation(my_id, friend_id)

        print(f"Chat started with {friend[1]}")

        receiver_thread = threading.Thread(target=background_receive, args=(convo_id, my_id), daemon=True)
        receiver_thread.start()

        while True:
            while not message_queue.empty():
                print(message_queue.get())

            msg = input("You: ")

            # Check again after input in case message was added mid-typing
            while not message_queue.empty():
                print(message_queue.get())

            if msg.lower() == "exit":
                print("Chat ended.")
                break

            send_message(convo_id, my_id, friend_id, msg)


    except Exception as e:
        print("An error occurred:", e)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()