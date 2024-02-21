import streamlit as st
import neo4j
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from googlesearch import search

st.set_page_config(
        page_title="Create Observatory",
)

from st_pages import show_pages_from_config

show_pages_from_config()

st.title("📝 Create a new observatory")

question = st.text_input(
    "Enter search terms",
    placeholder="accident+car",
)

#term = "accident+moto+grievement"
if question:
    st.write('Search with terms: ', question)
    
    results = search(question, lang="fr", num_results=50, advanced=True)
        
    # Neo4j connection details
    url = st.secrets["DB_URI"]
    username = st.secrets["DB_USER"]
    password = st.secrets["DB_PASSWORD"]
    
    # Create a driver instance
    driver = GraphDatabase.driver(url, auth=(username, password))

    # Function to add an event to the Neo4j database
    def add_article(session, url, description):
        session.run("MERGE (a:Article {url: $url}) ON CREATE SET a.description = $description, a.dateCreation=datetime()", url=url, description=description)

    def ajout_article(session, url, description, text):
        session.run("MERGE (a:Article {url: $url}) ON CREATE SET a.description = $description, a.text = $text, a.dateCreation=datetime()", url=url, description=description, text=text)

    def update_article(session, url, text):
        session.run("MATCH (a:Article {url: $url}) ON MATCH SET a.text = $text", url=url, text=text)

    with st.spinner('Collecting articles...'):
        # Insert data from the DataFrame
        
        with driver.session() as session:
            #for result in results:
             #   add_article(session, result.url, result.description)

            st.info('Enriching articles', icon="ℹ️")    
            for result in results:
                page = requests.get(result.url)
                soup = BeautifulSoup(page.content, "html.parser")
                paragraphs = soup.find_all("p", class_="")
                if paragraphs:
                    text = ""
                    for paragraph in paragraphs:
                        text = text + paragraph.text.strip()
                    if text:
                        # update_article(session, result.url, text)
                        ajout_article(session, result.url, result.description, text)   
            st.info('End of article enrichment', icon="ℹ️")    
    st.success('Collection of items completed!')        
    
    # Close the driver
    driver.close()
