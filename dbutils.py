import os

import discord
import json


def load_db(guild: discord.Guild) -> dict:
    # return this guild's entry in db.json
    db = _load_db()
    _validate_db(guild, db)
    return db[str(guild.id)]


def save_db(guild: discord.Guild, data: dict) -> None:
    current_db = _load_db()
    with open('db.json', 'w') as db:
        current_db[str(guild.id)] = data
        json.dump(current_db, db)


def _load_db():
    # load the entire db.json
    if not os.path.isfile('db.json'):
        with open('db.json', 'w') as db:
            db.write(json.dumps({}))
    with open('db.json', 'r') as db:
        return json.load(db)


def _validate_db(guild: discord.Guild, db: dict) -> None:
    # Validates db schema, repairing if necessary
    dirty = False
    if str(guild.id) not in db or 'enabled' not in db[str(guild.id)]:
        db[str(guild.id)] = {'enabled': False}
        dirty = True
    elif not isinstance(db[str(guild.id)]['enabled'], bool):
        db[str(guild.id)]['enabled'] = False
        dirty = True

    if dirty:
        save_db(guild, db[str(guild.id)])
