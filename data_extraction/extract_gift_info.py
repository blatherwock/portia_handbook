from collections import defaultdict
from enum import Enum

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import mapper, sessionmaker

import pdb

# Python Structs
npcs = []
props = []
strings = {}

class GiftRelationMixin():
    def __init__(self):
        super().__init__()
        self.gift_infos = []

    def add_gift_info(self, gift_info):
        self.gift_infos.append(gift_info)

    def loves(self):
        return sorted(self._gifts_at_level(GiftLevel.LOVE), key=lambda x: x.favor, reverse=True)

    def likes(self):
        return sorted(self._gifts_at_level(GiftLevel.LIKE), key=lambda x: x.favor, reverse=True)

    def dislikes(self):
        return sorted(self._gifts_at_level(GiftLevel.DISLIKE), key=lambda x: x.favor, reverse=True)

    def hates(self):
        return sorted(self._gifts_at_level(GiftLevel.HATE), key=lambda x: x.favor, reverse=True)

    def _gifts_at_level(self, level):
        return [info for info in self.gift_infos if info.gift_level == level]


class NPC(GiftRelationMixin):
    def __init__(self, db_data):
        super().__init__()
        self.db_data = db_data

    def __str__(self):
        return (f'{self.name}')

    def favor_info(self):
        return (f'Loves: {[gift.prop_str() for gift in self.loves()]}\n'
                f'Likes: {[gift.prop_str() for gift in self.likes()]}\n'
                f'Dislikes: {[gift.prop_str() for gift in self.dislikes()]}\n'
                f'Hates: {[gift.prop_str() for gift in self.hates()]}')

    @property
    def name(self):
        return strings[self.db_data.Name]

    @property
    def birthday(self):
        return self.db_data.Birthday

    @property
    def gift_id(self):
        return self.db_data.GiftID

    def include(self):
        people_to_exclude = ['Yoyo', 'First Child', 'Second Child']
        return (self.name not in people_to_exclude
                and 'SendGift' in self.db_data.Interact)


class PropType(Enum):
    COOKABLE_PC = 0
    COOKABLE_ACK = 1
    RELIC = 2
    CRAFTABLE = 3
    OTHER = 10


class Prop(GiftRelationMixin):
    def __init__(self, db_data, prop_type):
        super().__init__()
        self.db_data = db_data
        self._prop_type = prop_type

    def __str__(self):
        return (f'{self.name} - {self.prop_type} - {self.db_data.Props_Id}')

    def favor_info(self):
        return (f'Loved by: {[gift.npc_str() for gift in self.loves()]}\n'
                f'Liked by: {[gift.npc_str() for gift in self.likes()]}\n'
                f'Disliked by: {[gift.npc_str() for gift in self.dislikes()]}\n'
                f'Hated by: {[gift.npc_str() for gift in self.hates()]}')

    @property
    def name(self):
        return strings[self.db_data.Props_Name]

    @property
    def prop_type(self):
        return self._prop_type

    @property
    def gift_tag_ids(self):
        return self.db_data.Gift_TagID.split(",")

    @property
    def tag_list_ids(self):
        return self.db_data.Tag_List.split(",")

    def include(self):
        return (self.db_data.IsGift == "1")

class GiftLevel(Enum):
    LOVE = 0
    LIKE = 1
    DISLIKE = 3
    HATE = 4

class Gift():
    def __init__(self, npc, prop, gift_level, favor):
        self.npc = npc
        self.npc.add_gift_info(self)
        self.prop = prop
        self.prop.add_gift_info(self)
        self.gift_level = gift_level
        self.favor = favor

    def npc_str(self):
        return f'{self.npc.name} ({self.favor})'

    def prop_str(self):
        return f'{self.prop.name} ({self.favor})'


# DATABASE OBJECTS AND LOADING

class DB_NPC():
    pass

class DB_Props():
    pass

class DB_Gift():
    pass

class DB_TextString():
    pass

class DB_CookBook():
    pass

class DB_AckCookBook():
    pass

class DB_Relic():
    pass

class DB_Craft():
    pass

class DB_Assembly():
    pass

#----------------------------------------------------------------------
def loadSession():
    """"""
    dbPath = '../game_assets/game_db.db'
    engine = create_engine('sqlite:///%s' % dbPath, echo=False)

    metadata = MetaData(engine)
    db_npcs = Table('NpcRepository', metadata, Column("Id", String, primary_key=True), autoload=True)
    mapper(DB_NPC, db_npcs)

    props = Table('Props_total_table', metadata, Column("Props_id", String, primary_key=True), autoload=True)
    mapper(DB_Props, props)

    gifts = Table('Gift', metadata, Column("Gift_ID", String, primary_key=True), autoload=True)
    mapper(DB_Gift, gifts)

    texts = Table('Translation_hint', metadata, Column("ID", String, primary_key=True), autoload=True)
    mapper(DB_TextString, texts)

    cookbook = Table('Cook_Book', metadata, Column("ID", String, primary_key=True), autoload=True)
    mapper(DB_CookBook, cookbook)
    ack_cookbook = Table('Cook_AckList', metadata, Column("Food", String, primary_key=True), autoload=True)
    mapper(DB_AckCookBook, ack_cookbook)
    multipart_relic = Table('Repair_table', metadata, Column("Repair_Id", String, primary_key=True), autoload=True)
    mapper(DB_Relic, multipart_relic)
    craftable = Table('Synthesis_table', metadata, Column("Repair_Id", String, primary_key=True), autoload=True)
    mapper(DB_Craft, craftable)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def load_text(session):
    db_strings = session.query(DB_TextString).all()
    for s in db_strings:
        strings[s.ID] = s.English
    print(f'{len(strings)} strings loaded.')

def load_npcs(session):
    global npcs
    db_npcs = session.query(DB_NPC).all()
    for npc in db_npcs:
        loaded_npc = NPC(npc)
        if loaded_npc.include():
            npcs.append(loaded_npc)
    npcs = sorted(npcs, key=lambda x: x.name)
    print(f'{len(npcs)} npcs loaded.')

def load_props(session):
    global props
    db_props = session.query(DB_Props).all()
    food_props = [f[0] for f in session.query(DB_CookBook.Food)]
    ack_props = [f[0] for f in session.query(DB_AckCookBook.Food)]
    relic_props = [r[0] for r in session.query(DB_Relic.Item_Id)]
    craftable_props = [c[0] for c in session.query(DB_Craft.Item_Id)]

    for prop in db_props:
        prop_id = prop.Props_Id
        prop_type = PropType.OTHER
        if prop_id in food_props:
            prop_type = PropType.COOKABLE_PC
        elif prop_id in ack_props:
            prop_type = PropType.COOKABLE_ACK
        elif prop_id in relic_props:
            prop_type = PropType.RELIC
        elif prop_id in craftable_props:
            prop_type = PropType.CRAFTABLE

        loaded_prop = Prop(prop, prop_type)
        if loaded_prop.include():
            props.append(loaded_prop)
    props = sorted(props, key=lambda x: x.name)
    print(f'{len(props)} props loaded.')

def load_gifts(session):
    def _parse_favor(favor_input):
        '''
        input: "10|300_10$301_12$302_15$303_18$304_20"
        output: "(10, [(300, 10), (301, 12), (303, 18), (304, 20)])" which represents
        explanation: "(default favor value, [list of tuples: (tag list id, favor amount), ...]".
            tag list id corresponds to the Props_total_table.Tag_List column
        '''
        default_favor, exceptions = favor_input.split("|")
        exceptions = list(map(lambda x: tuple(x.split("_")), exceptions.split("$")))
        return (default_favor, exceptions)

    def _process_gift_level(gift_tagid_data, gift_favor_data, gift_level):
            gift_props = []
            for tag_id in gift_tagid_data.split(";"):
                gift_props.extend(props_by_gift_tagid[tag_id])

            default_favor, exceptions = _parse_favor(gift_favor_data)

            for prop in gift_props:
                prop_favor = default_favor
                # see if this prop is exceptional
                for tag_list_id in prop.tag_list_ids:
                    for exc in exceptions:
                        if tag_list_id == exc[0]:
                            prop_favor = exc[1]
                            break
                    if prop_favor != default_favor:
                        break
                Gift(npc, prop, gift_level, prop_favor)

    # invert the lookup so we can grab the appropriate npc or prop directly based on gift data
    npc_by_giftid = {}
    for npc in npcs:
        npc_by_giftid[npc.gift_id] = npc

    props_by_gift_tagid = defaultdict(list)
    for prop in props:
        for gift_tagid in prop.gift_tag_ids:
            props_by_gift_tagid[gift_tagid].append(prop)

    # load the gift information from DB
    db_gifts = session.query(DB_Gift).all()

    for gift_info in db_gifts:
        npc = npc_by_giftid.get(gift_info.Gift_ID)
        if npc is None:
            # could be gift for a NPC we have excluded. skip these
            continue

        _process_gift_level(gift_info.TagID_Excellent, gift_info.Favor_Excellent, GiftLevel.LOVE)
        _process_gift_level(gift_info.TagID_Like, gift_info.Favor_Like, GiftLevel.LIKE)
        _process_gift_level(gift_info.TagID_Dislike, gift_info.Favor_Dislike, GiftLevel.DISLIKE)
        _process_gift_level(gift_info.TagID_Hate, gift_info.Favor_Hate, GiftLevel.HATE)

if __name__ == "__main__":
    session = loadSession()
    load_text(session)
    load_props(session)
    load_npcs(session)

    load_gifts(session)

    # [print(npc) for npc in npcs]
    types = set()
    for prop in props:
        for p in prop.db_data.Item_Type.split(","):
            types.add(p)
    # print(types)

    [print(prop) for prop in props]



