import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import neo4j as neo4j
import googlesearch as googlesearch
import langchain
import langchain_community
import os
import st_pages
import streamlit_extras

st.set_page_config(
        page_title="Accidents finder",
)

#from streamlit_extras.app_logo import add_logo
#add_logo("images/icon_accidents.png", height=10)



from st_pages import show_pages_from_config

show_pages_from_config()

"""
# Accidents finder
"""

#st.image('images/chatgpt_accident.png', caption='Accidents', width=500)

# openai_api_key = st.secrets["OPENAI_KEY"]

from langchain_community.llms import OpenAI
from langchain_community.graphs import Neo4jGraph
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.embeddings.openai import OpenAIEmbeddings

os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_KEY"]
url = st.secrets["DB_URI"]
username = st.secrets["DB_USER"]
password = st.secrets["DB_PASSWORD"]
graph = Neo4jGraph(
    url=url,
    username=username,
    password=password
)


llm = OpenAI()

vectorstore = Neo4jVector.from_existing_graph(
    OpenAIEmbeddings(),
    url=url,
    username=username,
    password=password,
    index_name='articledescription',
    node_label="Article",
    text_node_properties=['title', 'description', 'text'],
    embedding_node_property='embedding',
)

vector_qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(), chain_type="stuff", retriever=vectorstore.as_retriever())

contextualize_query = """
match (node)-[:DOCUMENTS]->(e:Event)
WITH node AS a, e, score, {} as metadata limit 5
OPTIONAL MATCH (e)<-[:EXPLAINS]-(f:Factor)-[:EXPLAINS]->(e2:Event)
WITH a, e, score, metadata, apoc.text.join(collect(e2.description), ",") AS other_events
RETURN "Event : "+ e.description + " other events due to the same factor : " + coalesce(other_events, "") +"\n" as text, score, metadata
"""

contextualize_query1 = """
match (node)-[]->(e:Event)
WITH node AS a, e, score, {} as metadata limit 5
OPTIONAL MATCH (e)<-[:EXPLAINS]-(:Factor)
WITH a, e, i, f, score, metadata
RETURN "Title Article: "+ a.title + " description: "+ a.description + " factor: "+ coalesce(f.name, "")+ "\n" as text, score, metadata
"""

contextualized_vectorstore = Neo4jVector.from_existing_index(
    OpenAIEmbeddings(),
    url=url,
    username=username,
    password=password,
    index_name="articledescription",
    retrieval_query=contextualize_query,
)

vector_plus_context_qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(), chain_type="stuff", retriever=contextualized_vectorstore.as_retriever())

# Streamlit layout with tabs
container = st.container()
question = container.text_input("**:blue[Question:]**", "")

if question:
    tab1, tab2, tab3 = st.tabs(["No-RAG", "Basic RAG", "Augmented RAG"])
    with tab1:
        st.markdown("**:blue[No-RAG.] LLM only. Response generated from genIA only:**")
        st.write(llm(question))
    with tab2:
        st.markdown("**:blue[Basic RAG.] Response by vector search:**")
        st.write(vector_qa.run(question))
    with tab3:
        st.markdown("**:blue[Augmented RAG.] Response by vector search and context augmentation:**")
        st.write(vector_plus_context_qa.run(question))
