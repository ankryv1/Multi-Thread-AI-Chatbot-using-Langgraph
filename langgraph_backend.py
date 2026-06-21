from langgraph.graph import StateGraph, START, END, add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

##from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

llm = ChatGroq(model="llama-3.1-8b-instant")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

conn = sqlite.connect(database='chatbot.db', check_same_thread=False)

##checkpointer = InMemorySaver()
checkpointer = SqliteSaver(conn=conn)

def chat_node(state: ChatState):
    messages= state['messages']
    resp = llm.invoke(messages)
    return {'messages': [resp]}


graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer = checkpointer)

def retrive_all_threads():
    all_threads = set()

    for checkpoint in checkpoint.list(None):
        all_threads.add(checkpoint.config['cofigurable']['thread_id'])
        checkpoint.list()

#  list gives all values chexkpoints available
        print(checkpoint.list())

#  hum isme set bhi use kr skte hai kuki yaha saame multiple threads aayenge so set , un multiple me se single id hi aayengi