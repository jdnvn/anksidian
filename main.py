from anki_db import AnkiDB
import os
import time
from openai import OpenAI
import re
import json
from dotenv import load_dotenv

load_dotenv()

def get_last_modified(dir):
    # Expand user directory if necessary
    dir = os.path.expanduser(dir)
    
    # List all files in the directory
    files = [os.path.join(dir, f) for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    
    # Get the most recently modified file
    if not files:
        return None, None

    last_modified_file = max(files, key=os.path.getmtime)
    last_modified_time = os.path.getmtime(last_modified_file)

    return last_modified_file, last_modified_time

def build_prompt(**kwargs):
    prompt_template = open("prompt.txt", "r").read()
    for key, value in kwargs.items():
        prompt_template = prompt_template.replace("{" + key + "}", str(value))
    return prompt_template

def extract_tagged_content(raw_response, tag):
    tagged_content_regex = rf"<{tag}>(.*?)</{tag}>"
    matches = re.findall(tagged_content_regex, raw_response, re.DOTALL)
    return matches

def gpt(prompt):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    anki_profile_name = os.environ.get('ANKI_PROFILE_NAME')
    max_generated_cards = int(os.environ.get('MAX_GENERATED_CARDS'))
    obsidian_vault_dir = os.environ.get('OBSIDIAN_VAULT_DIR')

    last_modified_file, last_modified_time = get_last_modified(obsidian_vault_dir)
    current_time = time.time()
    
    # Calculate the time 24 hours ago
    one_day_ago = current_time - 24 * 60 * 60
    
    # Check if the timestamp is within the last day
    if last_modified_time < one_day_ago:
        print("The Obsidian vault hasn't been modified in the last 24 hours, skipping Anki import.")
        exit(1)

    notes = open(last_modified_file, "r").read()
    print(f"Notes:\n\n{notes}")

    # TODO: maybe include the date in the prompt
    # also emphasize that you do not need to follow the notes exactly, they could be wrong. Also feel free to add more important info on the back of the card
    prompt = build_prompt(notes=notes, max_cards=max_generated_cards)
    raw_response = gpt(prompt)

    flashcards_raw = extract_tagged_content(raw_response, "flashcards")
    flashcards = json.loads(flashcards_raw[0])

    print(f"Generated {len(flashcards)} flashcards:\n")
    for i, flashcard in enumerate(flashcards):
        print(f"Flashcard {i + 1}")
        print(f"Front: {flashcard['front']}")
        print(f"Back: {flashcard['back']}")
        print()

    cards_to_add = flashcards[:max_generated_cards]

    print("Adding generated cards to the Anki database...")

    db = AnkiDB(profile_name=anki_profile_name)
    cards = db.get_cards()

    for card in cards_to_add:
        front = card["front"]
        back = card["back"]
        db.create_card(front, back)

    print("Done.")
