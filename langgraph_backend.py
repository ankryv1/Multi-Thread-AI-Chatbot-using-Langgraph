from langgraph.graph import StateGraph, START, END, add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

from langgraph.checkpoint.memory import InMemorySaver

llm = ChatGroq(model="llama-3.1-8b-instant")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

checkpointer = InMemorySaver()

def chat_node(state: ChatState):
    messages= state['messages']
    resp = llm.invoke(messages)
    return {'messages': [resp]}


graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer = checkpointer)


