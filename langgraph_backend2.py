#   we will work with tools now
import os
from langgraph.graph import StateGraph, START, END, add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import sqlite3 
import requests
from langchain_core.tools import tool

# Now imports for RAG Tool

from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
    

# ---------------------

load_dotenv()

VANTAGE_API_KEY = os.getenv("VANTAGE_API_KEY")

##from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

llm = ChatGroq(model="llama-3.1-8b-instant")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

##checkpointer = InMemorySaver()
checkpointer = SqliteSaver(conn=conn)

#  define tools
def chat_node(state: ChatState):
    messages= state['messages']
    resp = llm_with_tools.invoke(messages)
    return {'messages': [resp]}


#   define tools 

search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calculator(first_num: float, second_num:float, operation: str):
    """Perform basic arithmatic operations on two numbers"""
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif(operation == 'div'):
            if second_num == 0:
                return {"error": "Division is not allowed"}
            result = first_num/second_num
            
        else:
            return {"error":"division by aero is not allowewd"}
        
        return {"result":result}
    except Exception as e:
        return{"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """Fetch the latest stock prices and get the result"""
    url = (f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={VANTAGE_API_KEY}")
    response= requests.get(url)
    return response.json()


@tool
def rag_tool(query: str):
    """Search the asked query for information form uploaded documents"""
    docs = vector_store.similarity_search(query, k=3)
    return "\n\n".join(doc.page_content for doc in docs)




tools = [get_stock_price, search_tool, calculator, rag_tool]
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)    #  Execute tool calls

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer = checkpointer)

def retrive_all_threads():
    all_threads = []

    for checkpoint in checkpointer.list(None):
        thread_id = checkpoint.config["configurable"]["thread_id"]

        if thread_id not in all_threads:
            all_threads.append(thread_id)

    return all_threads
#  hum isme set bhi use kr skte hai kuki yaha saame multiple threads aayenge so set , un multiple me se single id hi aayengi

#  function for pdf uploadation
def upload_create_vector(pdf_path):
    loader= PyPDFLoader(pdf_path)
    docs = loader.load("")

    splitter = RecursiveCharacterTextSplitter(chunk_size = 200, chunk_overlap = 20)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings()
    vector_store = Chroma(
    collection_name=f"lang-{thread_id}",
    embedding_function= embeddings,
    persist_directory='lang-chatDB'
    )

#   preventing rebulding vector database everytime
    if vector_store._collection.count() == 0:
        vector_store.add_documents(chunks)
        
    return vector_store