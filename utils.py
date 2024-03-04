# GPT-4 or GPT-3.5 Prompt to complete
@retry(tries=2, delay=5)
def process_gpt(system,
                prompt):

    completion = openai.ChatCompletion.create(
        # engine="gpt-3.5-turbo",
        model="gpt-3.5-turbo",
        max_tokens=2400,
        # Try to be as deterministic as possible
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
    )
    nlp_results = completion.choices[0].message.content
    return nlp_results

def run_completion(prompt, results, ctext):
    try:
      system = "You are an Accident Helper expert who extracts relevant information and stores it in a Neo4j knowledge graph"
      pr = Template(prompt).substitute(ctext=ctext)
      res = process_gpt(system, pr)
      results.append(json.loads(res.replace("\'", "'")))
      return results
    except Exception as e:
        print(e)

prompt1="""Since the description of the accident below, extract the entities and relationships described in the mentioned format:
0. ALWAYS COMPLETE THE RESPONSE. Never send partial responses.

1. First, look for these types of entities in the text and generate them in a format separated by commas, similar to the types of entities. The id property of each entity must be alphanumeric and unique among the entities. You will refer to this property to define the relationship between the entities. Do not create new types of entities that are not mentioned below. The document must be summarized and stored in the Article entity under the description property. You will need to generate as many entities as necessary according to the types below:
Entity Types:
label: 'Event', id: string, description: string, date: datetime, duration: string, location: string //Event is an event that occurred, for example, an accident
label: 'EventType', id: string, name: string //EventType the id property is the type of event that occurred
label: 'Article', id: string, urlMedia: string, uri: string, url: string, journalist: string, summary: string, date: datetime, title: string, media: string, description: string, text: string //Article Entity; the id property is the name of the article, in lowercase & camel-case & always starts with an alphabetical character. The text property must contain the full text of the article. The url field must be filled in by the internet link of the article
label: 'Document', id: string, description: string //Document Entity; the id property is the name of the document, in lowercase & camel-case & always starts with an alphabetical character
label: 'Factor', id: string, name: string // Factor Entity is the explanatory factor of the event; the id property is the name of the factor, in lowercase & camel-case & always starts with an alphabetical character
label: 'Solution', id: string, name: string, description: string, when: string // Solution Entity is the solution that could help resolve the event that occurred; the id property is the name of the factor, in lowercase & camel-case & always starts with an alphabetical character
label: 'Impact', id: string, name: string, description: string // Impact Entity is the impact of the event that occurred; the id property is the name of the impact, in lowercase & camel-case & always starts with an alphabetical character
label: 'Person', id: string, first_name: string, last_name: string, age: string, gender: string, nationality: string, profession: string, judicial_past: string // Person Entity is a person related to the event that occurred; the id property is the name of the person, in lowercase & camel-case & always starts with an alphabetical character
label: 'Group', id: string, name: string, nature: string, numberMembers: integer // Group Entity is a group to which a person is linked; the id property is the name of the group, in lowercase & camel-case & always starts with an alphabetical character
2. Then, generate each relationship as a triplet of source, relation, and target. To refer to the source entity and the target entity, use their respective id property. You will need to generate as many relationships as necessary, as defined below:
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
