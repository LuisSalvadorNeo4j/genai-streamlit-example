import streamlit as st
import neo4j
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from googlesearch import search
import openai
from retry import retry
import re
from string import Template
import json
import ast
import time
import pandas as pd
import glob
from timeit import default_timer as timer

st.set_page_config(
        page_title="New Observatory",
)

from st_pages import show_pages_from_config

show_pages_from_config()

st.title("🆕 New accident observatory")

constraints_cyp="""
CREATE CONSTRAINT node_key_personne_id IF NOT EXISTS FOR (n:Personne) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_groupe_id IF NOT EXISTS FOR (n:Groupe) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_impact_id IF NOT EXISTS FOR (n:Impact) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_typeevent_id IF NOT EXISTS FOR (n:TypeEvent) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_factor_id IF NOT EXISTS FOR (n:Factor) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_solution_id IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS NODE KEY;
"""

constraint_personne_id = """
CREATE CONSTRAINT node_key_personne_id IF NOT EXISTS FOR (n:Personne) REQUIRE n.id IS NODE KEY;
"""
constraint_groupe_id = """
CREATE CONSTRAINT node_key_groupe_id IF NOT EXISTS FOR (n:Groupe) REQUIRE n.id IS NODE KEY;
"""
constraint_impact_id = """
CREATE CONSTRAINT node_key_impact_id IF NOT EXISTS FOR (n:Impact) REQUIRE n.id IS NODE KEY;
"""
constraint_event_id = """
CREATE CONSTRAINT node_key_event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS NODE KEY;
"""
constraint_typeevent_id = """
CREATE CONSTRAINT node_key_typeevent_id IF NOT EXISTS FOR (n:TypeEvent) REQUIRE n.id IS NODE KEY;
"""
constraint_article_id = """
CREATE CONSTRAINT node_key_article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS NODE KEY;
"""
constraint_document_id = """
CREATE CONSTRAINT node_key_document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS NODE KEY;
"""
constraint_factor_id = """
CREATE CONSTRAINT node_key_factor_id IF NOT EXISTS FOR (n:Factor) REQUIRE n.id IS NODE KEY;
"""
constraint_solution_id = """
CREATE CONSTRAINT node_key_solution_id IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS NODE KEY;
"""


prompt1="""Since the description of the accident below, extract the entities and relationships described in the mentioned format:
0. ALWAYS COMPLETE THE RESPONSE. Never send partial responses.
1. First, look for these types of entities in the text and generate them in a format separated by commas, similar to the types of entities. The `id` property of each entity must be alphanumeric and unique among the entities. You will refer to this property to define the relationship between the entities. Do not create new types of entities that are not mentioned below. The document must be summarized and stored in the Article entity under the `description` property. You will need to generate as many entities as necessary according to the types below:
    Entity Types:
    label: 'Event', id: string, description: string, date: datetime, duration: string, location: string //Event is an event that occurred, for example, an accident
    label: 'EventType', id: string, name: string //EventType the `id` property is the type of event that occurred
    label: 'Article', id: string, urlMedia: string, uri: string, url: string, journalist: string, summary: string, date: datetime, title: string, media: string, description: string, text: string //Article Entity; the `id` property is the name of the article, in lowercase & camel-case & always starts with an alphabetical character. The `text` property must contain the full text of the article. The `url` field must be filled in by the internet link of the article
    label: 'Document', id: string, description: string //Document Entity; the `id` property is the name of the document, in lowercase & camel-case & always starts with an alphabetical character
    label: 'Factor', id: string, name: string // Factor Entity is the explanatory factor of the event; the `id` property is the name of the factor, in lowercase & camel-case & always starts with an alphabetical character
    label: 'Solution', id: string, name: string, description: string, when: string // Solution Entity is the solution that could help resolve the event that occurred; the `id` property is the name of the factor, in lowercase & camel-case & always starts with an alphabetical character
    label: 'Impact', id: string, name: string, description: string // Impact Entity is the impact of the event that occurred; the `id` property is the name of the impact, in lowercase & camel-case & always starts with an alphabetical character
    label: 'Person', id: string, first_name: string, last_name: string, age: string, gender: string, nationality: string, profession: string, judicial_past: string // Person Entity is a person related to the event that occurred; the `id` property is the name of the person, in lowercase & camel-case & always starts with an alphabetical character
    label: 'Group', id: string, name: string, nature: string, numberMembers: integer // Group Entity is a group to which a person is linked; the `id` property is the name of the group, in lowercase & camel-case & always starts with an alphabetical character
2. Then, generate each relationship as a triplet of source, relation, and target. To refer to the source entity and the target entity, use their respective `id` property. You will need to generate as many relationships as necessary, as defined below:
    Relationship Types:
    Person|INJURES|Person
    Person|KILLS|Person
    Person|KNOWS|Person
    Person|RELATED_TO|Person
    Person|PART_OF|Group
    Person|WANTS_TO_BE_PART_OF|Group
    Person|INFLUENCES|Group
    Person|LEADS|Group
    Person|VICTIM_OF|Event
    Person|AUTHOR_OF|Event
    Person|INVOLVED_IN|Event
    Person|DOCUMENTS|Event
    Person|WITNESS_OF|Event
    Person|COVICTIM_OF|Event
    Event|HAS|Impact
    Impact|ON|Person
    Event|FOLLOWS|Event
    Event|HAS|EventType
    Article|DOCUMENTS|Event
    Document|PROVES|Event
    Factor|EXPLAINS|Event
    Event|HAS|Solution

The result should look like:
{
    "entities": [{"label":"Event","id":string,"description":string,"date":datetime,"duration":string,"location":string}],
    "relations": [{"source":string',"relation":string,"target":string}]
}
Accident :
$ctext
"""

openai.api_key = st.secrets["OPENAI_KEY"]

#nbResSearch = st.secrets["NB_RES_SEARCH"]

# GPT-4 or GPT-3.5 Prompt to complete
@retry(tries=2, delay=5)
def process_gpt(system,
                prompt):

    #completion = openai.ChatCompletion.create(
        # engine="gpt-3.5-turbo",
        #model="gpt-3.5-turbo",
        #max_tokens=2400,
        #model="gpt-4",
        #max_tokens=4096,
        # Try to be as deterministic as possible
        #temperature=0,
        #messages=[
            #{"role": "system", "content": system},
            #{"role": "user", "content": prompt},
        #]
    #)
    completion = openai.chat.completions.create(
      model="gpt-3.5-turbo",
      temperature=0,
      messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
      ],
    ) 

    nlp_results = completion.choices[0].message.content
    return nlp_results

def clean_text(text):
  clean = "\n".join([row for row in text.split("\n")])
  clean = re.sub(r'\(fig[^)]*\)', '', clean, flags=re.IGNORECASE)
  return clean

def run_completion(prompt, results, ctext):
    try:
      system = "You are an Accident Expert Helper who extracts relevant information and stores it in a Neo4j knowledge graph."
      pr = Template(prompt).substitute(ctext=ctext)
      res = process_gpt(system, pr)
      results.append(json.loads(res.replace("\'", "'")))
      return results
    except Exception as e:
        print(e)

#pre-processing results for uploading into Neo4j - helper function:
def get_prop_str(prop_dict, _id):
    s = []
    for key, val in prop_dict.items():
      if key != 'label' and key != 'id':
         s.append(_id+"."+key+' = "'+str(val).replace('\"', '"').replace('"', '\"')+'"')
    return ' ON CREATE SET ' + ','.join(s)

def get_cypher_compliant_var(_id):
    return "_"+ re.sub(r'[\W_]', '', _id)

def generate_cypher(in_json):
    e_map = {}
    e_stmt = []
    r_stmt = []
    e_stmt_tpl = Template("($id:$label{id:'$key'})")
    r_stmt_tpl = Template("""
      MATCH $src
      MATCH $tgt
      MERGE ($src_id)-[:$rel]->($tgt_id)
    """)
    for obj in in_json:
      for j in obj['entities']:
          props = ''
          label = j['label']
          id = j['id']
          if label == 'Group':
            id = 'g'+str(time.time_ns())
          elif label == 'Person':
            id = 'p'+str(time.time_ns())
          elif label == 'Event':
            id = 'e'+str(time.time_ns())
          elif label == 'EventType':
            id = 'te'+str(time.time_ns())
          elif label == 'Article':
            id = 'a'+str(time.time_ns())
          elif label == 'Document':
            id = 'd'+str(time.time_ns())
          elif label == 'Factor':
            id = 'f'+str(time.time_ns())
          elif label == 'Solution':
            id = 's'+str(time.time_ns())
          elif label == 'Impact':
            id = 'i'+str(time.time_ns())
          else:
            id = 'z'+str(time.time_ns())
          # print(j['id'])
          varname = get_cypher_compliant_var(j['id'])
          stmt = e_stmt_tpl.substitute(id=varname, label=label, key=id)
          e_map[varname] = stmt
          e_stmt.append('MERGE '+ stmt + get_prop_str(j, varname))
          print(e_stmt)

      for st in obj['relations']:
          print(st)
          #rels = st.split("|")
          #rels = st.split(",")
          #print(rels)
          src_id = get_cypher_compliant_var(st['source'])
          rel = st['relation']
          tgt_id = get_cypher_compliant_var(st['target'])
          #src_id = get_cypher_compliant_var(rels[0].strip())
          #rel = rels[1]
          #tgt_id = get_cypher_compliant_var(rels[2].strip())
          #print(src_id)
          #print(rel)
          #print(tgt_id)
          stmt = r_stmt_tpl.substitute(
              src_id=src_id, tgt_id=tgt_id, src=e_map[src_id], tgt=e_map[tgt_id], rel=rel)
          print(stmt)
          r_stmt.append(stmt)

    return e_stmt, r_stmt

def graph_article(session, text):
  prompts = [prompt1]
  results = []
  for p in prompts:
    results = run_completion(p, results, clean_text(text))
    if results:
      ent_cyp, rel_cyp = generate_cypher(results)
      # ingérer les entités
      st.info('Ingestion of entities', icon="ℹ️") 
      st.info(ent_cyp, icon="ℹ️")
      for req_ent in ent_cyp:
        session.run(req_ent)
      # ingérer les relations
      st.info('Ingestion of relations', icon="ℹ️") 
      st.info(rel_cyp, icon="ℹ️")
      for req_rel in rel_cyp:
        session.run(req_rel)
    

question = st.text_input(
    "Enter search terms",
    placeholder="accident+car",
)

#term = "accident+moto+grievement"
if question:
    st.write('Searching with the terms: ', question)
    
    results = search(question, lang="en", num_results=3, advanced=True)
        
    # Neo4j connection details
    url = st.secrets["DB_URI"]
    username = st.secrets["DB_USER"]
    password = st.secrets["DB_PASSWORD"]
    
    # Create a driver instance
    driver = GraphDatabase.driver(url, auth=(username, password))        

    with st.spinner('Collecting articles...'):
        # Insert data from the DataFrame
        
        with driver.session() as session:
            #st.info('Updating constraints', icon="ℹ️")    
            #session.run(constraint_personne_id)
            #session.run(constraint_groupe_id)
            #session.run(constraint_impact_id)
            #session.run(constraint_event_id)
            #session.run(constraint_typeevent_id)
            #session.run(constraint_article_id)
            #session.run(constraint_document_id)
            #session.run(constraint_factor_id)
            #session.run(constraint_solution_id)    

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
                        #st.info('text : ' + text, icon="ℹ️")
                        # update_article(session, result.url, text)
                        graph_article(session, text)   
            st.info('End of article enrichment', icon="ℹ️")    
    st.success('Collection of items completed!')         
    
    # Close the driver
    driver.close()
