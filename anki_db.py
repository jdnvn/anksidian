import os
from utils import checksum, guid
import time
import sqlite3

class AnkiDB:
    UNIT_SEPARATOR = chr(31)

    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.file_path = self.db_path(profile_name)

    def db_path(self, profile_name):
        return os.path.expanduser(f"~/Library/Application Support/Anki2/{profile_name}/collection.anki2")

    def create_note(self, front, back):
        fields = f"{front}{self.UNIT_SEPARATOR}{back}"
        csum = checksum(fields)

        timestamp = int(time.time() * 1000)  # Milliseconds
        model_ids = self.get_all_notetype_ids()
        default_model_id = model_ids[0]

        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()
        # Insert the new note into the 'notes' table
        cursor.execute('''
            INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,  # id (None for auto-increment)
            guid(),  # guid (or generate a random GUID)
            default_model_id,  # mid (model ID, you must specify the correct model ID)
            timestamp // 1000,  # mod (last modified time)
            -1,  # usn (update sequence number, use -1 for local updates)
            '',  # tags (empty string for no tags)
            fields,  # flds (combined fields)
            front,  # sfld (sort field, usually the front of the card)
            csum,  # csum (checksum, Anki uses this for duplicates)
            0,  # flags (card flags)
            ''   # data (extra data, usually empty)
        ))

        # Commit the changes to the database
        conn.commit()
        conn.close()

        return timestamp
    
    def create_card(self, front, back):
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()

        timestamp = int(time.time() * 1000)  # Milliseconds
        note_id = self.create_note(front, back)

        # Insert a corresponding card (note that this requires more detailed setup)
        cursor.execute('''
            INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,  # id (None for auto-increment)
            note_id,  # nid (note ID from the inserted note)
            1,  # did (deck ID, specify the correct deck ID)
            0,  # ord (card template number, 0 for the first template)
            timestamp // 1000,  # mod (last modified time)
            -1,  # usn (update sequence number, use -1 for local updates)
            0,  # type (0 for new cards)
            0,  # queue (0 for new cards)
            1,  # due (due date for review)
            0,  # ivl (interval, 0 for new cards)
            2500,  # factor (ease factor, 2500 for default)
            0,  # reps (number of reviews)
            0,  # lapses (number of lapses)
            0,  # left (used by the scheduler)
            0,  # odue (original due date, 0 for no original due date)
            0,  # odid (original deck ID, 0 for no original deck)
            0,  # flags (card flags)
            '{}'   # data (extra data, usually empty)
        ))

        # Commit the changes to the database
        conn.commit()
        conn.close()

        return timestamp
    
    def get_cards(self):
        conn = sqlite3.connect(self.file_path)

        cursor = conn.cursor()
        cursor.execute('''
            SELECT cards.id, notes.flds 
            FROM cards 
            JOIN notes ON cards.nid = notes.id 
            LIMIT 10
        ''')
        results = cursor.fetchall()
        conn.close()

        cards = []
        for result in results:
            card_id, fields = result
            field_list = fields.split(self.UNIT_SEPARATOR)
            cards.append({"id": card_id, "front": field_list[0], "back": field_list[1]})
        return cards
    
    def get_all_notetype_ids(self):
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM notetypes')
        results = cursor.fetchall()
        conn.close()
        return [result[0] for result in results]
    
    def delete_card(self, card_id):
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()

        # Delete the card from the 'cards' table
        cursor.execute('''
            DELETE FROM cards WHERE id = ?
        ''', (card_id,))

        # Delete the note from the 'notes' table
        cursor.execute('''
            DELETE FROM notes WHERE id = ?
        ''', (card_id,))

        # Commit the changes to the database
        conn.commit()
        conn.close()

