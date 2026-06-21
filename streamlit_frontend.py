import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

from langgraph_backend2 import workflow, retrive_all_threads

# =====================================================
# Utility Functions
# =====================================================

def generate_thread_id():
    """Generate a unique conversation id."""
    return str(uuid.uuid4())


def add_thread(thread_id):
    """Add thread to sidebar if not already present."""
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
     return workflow.get_state(config= {"configurable":{'thread_id': thread_id}}).values['messages']

def reset_chat():
    """Start a completely new conversation."""
    new_thread = generate_thread_id()

    st.session_state["thread_id"] = new_thread
    st.session_state["message_history"] = []

    add_thread(new_thread)


# =====================================================
# Session State Initialization
# =====================================================

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrive_all_threads()

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

# Add current thread to sidebar
add_thread(st.session_state["thread_id"])


# =====================================================
# Sidebar
# =====================================================

st.sidebar.title("LangGraph Chatbot")

uploaded_file= st.sidebar.file_uploader("Upload a PDF", type=["pdf"])

if st.sidebar.button("➕ New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state["chat_threads"]:

    if st.sidebar.button(thread_id):
        st.session_state["thread_id"] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state["message_history"] = temp_messages
# =====================================================
# Display Existing Messages
# =====================================================

for msg in st.session_state["message_history"]:

    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# =====================================================
# Chat Input
# =====================================================

user_input = st.chat_input("Type here...")

CONFIG = {
    "configurable": {
        "thread_id": st.session_state["thread_id"]
    }
}


# =====================================================
# User sends a message
# =====================================================

if user_input:

    # Save user message
    st.session_state["message_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Generator for streaming AI response
    def generate_response():

        for message, metadata in workflow.stream(

            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            },

            config=CONFIG,

            stream_mode="messages",

        ):

            if message.content:
                yield message.content

    # Display streaming response
    with st.chat_message("assistant"):

        ai_message = st.write_stream(generate_response())

    # Save assistant message
    st.session_state["message_history"].append(

        {
            "role": "assistant",
            "content": ai_message,
        }

    )

