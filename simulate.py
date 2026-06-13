# simulate_poetryquill.py
# Generates pseudo-realistic activity data for PoetryQuill
# Uses Option B — direct profile inserts with fake UUIDs (bypasses auth)
# Run once to populate your Supabase with realistic demo data

import os
import random
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import time

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# ── DATA POOLS ──────────────────────────────────────────────

USERNAMES = [
    "ink_and_starlight", "velvet_verses", "morningpage_maya", "quietstorm_writes",
    "the_paper_poet", "lune_and_letters", "wandering_stanza", "echo_in_margins",
    "salt_and_syllables", "dusk_writer", "neon_haiku", "threadbare_thoughts",
    "river_of_lines", "fog_and_form", "the_blank_page", "worn_pages_william",
    "syllable_seeker", "between_the_lines_b", "typewriter_soul", "midnight_draft",
    "soft_punctuation", "comma_and_clause", "verse_and_vigil", "the_long_form",
    "open_couplet", "lyric_in_blue", "prose_and_patience", "the_still_point",
    "overture_olivia", "scattered_stanzas", "half_rhyme_hugo", "the_enjambment",
    "syntax_and_sorrow", "cadence_keeper", "iambic_iris", "free_verse_felix",
    "the_volta", "white_space_writer", "margin_notes_mira", "final_draft_finn"
]

DISPLAY_NAMES = [
    "Maya Chen", "William Foster", "Iris Nakamura", "Felix Okonkwo",
    "Olivia Reyes", "Hugo Martens", "Mira Patel", "Finn O'Brien",
    "Luna Vasquez", "Echo Park", "River Stone", "Dawn Mitchell",
    "Ash Winters", "Sage Collins", "Reed Morrison", "Wren Elliot",
    "Clay Harper", "Fern Huang", "Zara Ahmed", "Theo Novak",
    "Priya Sharma", "Arjun Mehta", "Ananya Iyer", "Rohan Das",
    "Divya Krishnan", "Vikram Nair", "Neha Gupta", "Arun Pillai",
    "Sana Sheikh", "Kabir Malhotra", "Leila Ahmadi", "Omar Hassan",
    "Sofia Rossi", "Luca Bianchi", "Emma Laurent", "Jules Moreau",
    "Hana Tanaka", "Kenji Yamamoto", "Min-Ji Park", "Yuna Kim"
]

BIOS = [
    "Writing through the fog. Coffee dependent. Probably overthinking.",
    "Former academic, recovering perfectionist. Poetry is cheaper than therapy.",
    "I write about the ocean even though I live in a landlocked city.",
    "Collecting words the way other people collect regrets.",
    "Night shift poet. Everything looks different at 3am.",
    "Still figuring out what I'm trying to say. That's the point.",
    "Words are the only architecture I know how to build.",
    "Reading everything. Writing too slowly. Feeling too much.",
    "Somewhere between a draft and a finished thought.",
    "I write so I remember what it felt like to be here.",
    None, None, None  # some users have no bio — realistic
]

POEM_TITLES = [
    "Midnight Cartography", "The Weight of Small Things", "After the Last Train",
    "Peripheral Vision", "What the River Knows", "Salt Flat Memory",
    "Things I Didn't Say at the Funeral", "Almost Tuesday", "Borrowed Light",
    "The Long Way Home", "Threshold", "What Remains", "Before the Birds",
    "November Light", "Loose Ends", "Half-Life", "Sea Glass",
    "The Space Between Words", "Letters Never Sent", "Ordinary Magic",
    "Untitled III", "For No One in Particular", "Becoming",
    "The Quiet Hours", "After the Storm", "Golden Hour",
    "Forgotten Dreams", "Echoes of Yesterday", "The Last Rain",
    "Between the Stars", "Small Mercies", "Morning Ritual",
    "When You're Not Looking", "Cartography of Loss", "Static",
    "Revision", "Draft", "First Light", "The Hours", "Watershed"
]

POEM_CONTENTS = [
    """The moon forgets itself
in the still water below—
I wonder if it minds.

Some nights I do the same,
lose my edges in reflection,
become whatever surface
is calm enough to hold me.""",

    """You left your coffee cup
on the windowsill again.
I haven't moved it.

It's been three weeks
and I've started to think
that some things
are better left
where they were last held.""",

    """There's a word in Portuguese—
saudade—
for the presence of absence,
the shape a thing leaves
when it's gone.

I've been fluent in it
longer than I've known the word.""",

    """I keep finding things
I thought I had lost
in places I haven't been.

This is what it means
to live in a body—
to be always
slightly ahead of yourself,
or behind.""",

    """The city at 3am
holds its breath
between the last train
and the first.

I've stood on that platform
longer than I'll admit,
watching the rails
go cold.""",

    """We were very good
at being almost happy
for a very long time.

I think that counts for something.
I'm still deciding what.""",

    """On the last day of summer
the light turned amber
and stayed that way
until dark.

I didn't photograph it.
Some things
you have to let
be only yours.""",

    """Every photograph
contains a version of me
I can no longer reach.

She looks like she's about to say something.
She never does.""",

    """The dog knows before I do
that something has shifted.
She watches the door
with a patience
I've never managed.

I'm learning from her
to trust what I can't name.""",

    """I wrote your name in sand
and waited for the tide.
It came.
It always does.

That's the thing about ocean—
it doesn't hesitate.""",

    """Some days the light
comes through at the wrong angle
and I see everything:

the dust on the shelves,
the crack in the ceiling,
the life I'm living
instead of the one
I planned.""",

    """Between the pages
of every book I've finished,
your name lives on.

I didn't put it there.
That's how I know
it's true.""",

    """There's a version of this poem
where I say exactly
what I mean.

I'm still writing it.
I may never finish.
Some poems
are practice
for the real thing.""",

    """The garden this year
grew everything I planted
and several things I didn't.

That feels like a metaphor.
I'm leaving it there.""",

    """I keep the windows closed
not because of the cold
but because of the quiet.

The quiet here
sounds like something
I'm not ready
to name."""
]

TAGS_POOL = [
    ["grief", "memory"], ["nature", "seasons"], ["love", "loss"],
    ["identity", "self"], ["city", "urban"], ["night", "solitude"],
    ["family", "home"], ["time", "change"], ["hope", "healing"],
    ["longing", "distance"], ["quiet", "stillness"], ["ocean", "water"],
    ["light", "shadow"], ["body", "mind"], [], []  # some untagged
]

COMMENT_TEXTS = [
    "This hit me differently today.",
    "The last line stays with you.",
    "Beautiful imagery throughout.",
    "I needed to read this today.",
    "The rhythm here is perfect.",
    "This is quietly devastating.",
    "Saved this one.",
    "The way you use space here is everything.",
    "I keep coming back to the second stanza.",
    "This is the kind of poem that changes shape each time you read it.",
    "Exactly what I couldn't say.",
    "The simplicity here is deceptive — there's so much underneath.",
    "This made me stop scrolling.",
    "Wrote this down in my notebook.",
    "The ending is a gut punch.",
    "I've read this four times now.",
    "You said something I didn't know needed saying.",
    "The enjambment in the third stanza is doing so much work.",
    "This is what I come here for.",
    "Quietly one of the best things I've read this month.",
]

COUNTRIES = ["us", "in", "gb", "ca", "au", "de", "fr", "jp", "br", "global"]


# ── HELPERS ─────────────────────────────────────────────────

def random_date(days_back_min=1, days_back_max=180):
    """Realistic datetime with evening/weekend clustering."""
    days_back = random.randint(days_back_min, days_back_max)
    base = datetime.now() - timedelta(days=days_back)

    # Weight toward evenings — real writing platform behavior
    hour = random.choices(
        range(24),
        weights=[1,1,1,1,1,1,2,3,4,4,4,5,5,5,5,6,6,7,8,8,7,6,4,2]
    )[0]

    return base.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0
    ).astimezone().isoformat()


def power_law_likes(max_val=120):
    """Power law: few posts get many likes, most get few. Realistic."""
    return min(int(random.paretovariate(1.2)), max_val)


def power_law_views(likes):
    """Views are always higher than likes — typically 5-20x."""
    multiplier = random.uniform(5, 20)
    return int(likes * multiplier) + random.randint(0, 50)


# ── STEP 1: CREATE PROFILES ──────────────────────────────────

def create_profiles(count=35):
    print(f"\n{'='*50}")
    print(f"STEP 1: Creating {count} profiles...")
    print('='*50)

    profile_ids = []
    usernames_shuffled = random.sample(USERNAMES, min(count, len(USERNAMES)))

    for i in range(count):
        profile_id = str(uuid.uuid4())
        username = usernames_shuffled[i]
        display_name = DISPLAY_NAMES[i % len(DISPLAY_NAMES)]
        bio = random.choice(BIOS)
        signup_date = random_date(days_back_min=60, days_back_max=365)

        # User type distribution — realistic
        # Power users: high poem count
        # Regular: moderate
        # Lurkers: low
        user_type = random.choices(
            ["power", "regular", "lurker"],
            weights=[15, 45, 40]
        )[0]

        poem_count = {
            "power": random.randint(8, 25),
            "regular": random.randint(2, 7),
            "lurker": random.randint(0, 1)
        }[user_type]

        follower_count = {
            "power": random.randint(20, 150),
            "regular": random.randint(2, 30),
            "lurker": random.randint(0, 5)
        }[user_type]

        points = random.randint(0, 500)

        try:
            result = supabase.table("profiles").insert({
                "id": profile_id,
                "username": username,
                "display_name": display_name,
                "bio": bio,
                "follower_count": follower_count,
                "following_count": random.randint(0, follower_count + 10),
                "poem_count": poem_count,
                "points": points,
                "total_points_earned": points + random.randint(0, 200),
                "current_streak": random.randint(0, 14),
                "longest_streak": random.randint(0, 30),
                "country": random.choice(COUNTRIES),
                "created_at": signup_date,
                "updated_at": signup_date,
            }).execute()

            if result.data:
                profile_ids.append(profile_id)
                print(f"  ✓ [{user_type:7}] @{username}")

        except Exception as e:
            print(f"  ✗ Failed @{username}: {e}")

        time.sleep(0.08)

    print(f"\n  → Created {len(profile_ids)}/{count} profiles")
    return profile_ids


# ── STEP 2: CREATE POEMS ─────────────────────────────────────

def create_poems(profile_ids, count=55):
    print(f"\n{'='*50}")
    print(f"STEP 2: Creating {count} poems...")
    print('='*50)

    poem_ids = []
    titles = random.sample(POEM_TITLES, min(count, len(POEM_TITLES)))
    # If count > available titles, repeat some
    while len(titles) < count:
        titles.append(random.choice(POEM_TITLES) + " (II)")

    for i in range(count):
        author_id = random.choice(profile_ids)
        like_count = power_law_likes()
        view_count = power_law_views(like_count)
        publish_date = random_date(days_back_min=1, days_back_max=150)

        try:
            result = supabase.table("poems").insert({
                "author_id": author_id,
                "title": titles[i],
                "content": random.choice(POEM_CONTENTS),
                "tags": random.choice(TAGS_POOL),
                "is_published": True,
                "like_count": like_count,
                "view_count": view_count,
                "comment_count": 0,  # updated when comments inserted
                "published_at": publish_date,
                "created_at": publish_date,
                "updated_at": publish_date,
            }).execute()

            if result.data:
                poem_id = result.data[0]["id"]
                poem_ids.append(poem_id)
                print(f"  ✓ '{titles[i]}' ({like_count} likes, {view_count} views)")

        except Exception as e:
            print(f"  ✗ Failed '{titles[i]}': {e}")

        time.sleep(0.08)

    print(f"\n  → Created {len(poem_ids)}/{count} poems")
    return poem_ids


# ── STEP 3: CREATE LIKES ─────────────────────────────────────

def create_likes(profile_ids, poem_ids, count=120):
    print(f"\n{'='*50}")
    print(f"STEP 3: Creating {count} likes...")
    print('='*50)

    pairs_used = set()
    created = 0
    attempts = 0

    while created < count and attempts < count * 4:
        user_id = random.choice(profile_ids)
        poem_id = random.choice(poem_ids)
        pair = (user_id, poem_id)

        if pair in pairs_used:
            attempts += 1
            continue

        pairs_used.add(pair)

        try:
            supabase.table("likes").insert({
                "user_id": user_id,
                "poem_id": poem_id,
                "created_at": random_date(days_back_min=1, days_back_max=120),
            }).execute()
            created += 1
            if created % 20 == 0:
                print(f"  ✓ {created}/{count} likes created")

        except Exception as e:
            print(f"  ✗ Like error: {e}")

        attempts += 1
        time.sleep(0.04)

    print(f"\n  → Created {created}/{count} likes")


# ── STEP 4: CREATE COMMENTS ──────────────────────────────────

def create_comments(profile_ids, poem_ids, count=70):
    print(f"\n{'='*50}")
    print(f"STEP 4: Creating {count} comments...")
    print('='*50)

    comment_ids = []
    created = 0

    for i in range(count):
        poem_id = random.choice(poem_ids)
        author_id = random.choice(profile_ids)
        comment_date = random_date(days_back_min=1, days_back_max=100)

        try:
            result = supabase.table("comments").insert({
                "poem_id": poem_id,
                "author_id": author_id,
                "content": random.choice(COMMENT_TEXTS),
                "like_count": random.randint(0, 8),
                "created_at": comment_date,
                "updated_at": comment_date,
            }).execute()

            if result.data:
                comment_ids.append(result.data[0]["id"])
                created += 1
                if created % 20 == 0:
                    print(f"  ✓ {created}/{count} comments created")

        except Exception as e:
            print(f"  ✗ Comment error: {e}")

        time.sleep(0.04)

    print(f"\n  → Created {created}/{count} comments")
    return comment_ids


# ── STEP 5: CREATE FOLLOWS ───────────────────────────────────

def create_follows(profile_ids, count=80):
    print(f"\n{'='*50}")
    print(f"STEP 5: Creating {count} follows...")
    print('='*50)

    pairs_used = set()
    created = 0
    attempts = 0

    while created < count and attempts < count * 4:
        follower_id = random.choice(profile_ids)
        following_id = random.choice(profile_ids)

        # Can't follow yourself
        if follower_id == following_id:
            attempts += 1
            continue

        pair = (follower_id, following_id)
        if pair in pairs_used:
            attempts += 1
            continue

        pairs_used.add(pair)

        try:
            supabase.table("follows").insert({
                "follower_id": follower_id,
                "following_id": following_id,
                "created_at": random_date(days_back_min=1, days_back_max=150),
            }).execute()
            created += 1
            if created % 20 == 0:
                print(f"  ✓ {created}/{count} follows created")

        except Exception as e:
            print(f"  ✗ Follow error: {e}")

        attempts += 1
        time.sleep(0.04)

    print(f"\n  → Created {created}/{count} follows")


# ── STEP 6: CREATE COLLECTIONS ───────────────────────────────

def create_collections(profile_ids, poem_ids, count=15):
    print(f"\n{'='*50}")
    print(f"STEP 6: Creating {count} collections...")
    print('='*50)

    collection_names = [
        "Poems for 3am", "Things That Made Me Stop Scrolling",
        "The Ocean Series", "Grief & Growing", "Quiet Favorites",
        "Poems I Wish I'd Written", "Autumn Reading List",
        "For Hard Days", "Love in Small Moments", "The Long Poems",
        "Short and Devastating", "Morning Reads", "Night Pages",
        "Works in Progress", "The Classics"
    ]

    collection_ids = []
    created = 0

    for i in range(min(count, len(collection_names))):
        user_id = random.choice(profile_ids)
        create_date = random_date(days_back_min=10, days_back_max=120)

        try:
            result = supabase.table("collections").insert({
                "user_id": user_id,
                "name": collection_names[i],
                "description": random.choice([
                    "A collection of poems that found me at the right time.",
                    "Curated for the in-between moments.",
                    "Things worth returning to.",
                    None
                ]),
                "is_public": random.choice([True, True, True, False]),
                "poem_count": 0,
                "created_at": create_date,
                "updated_at": create_date,
            }).execute()

            if result.data:
                collection_id = result.data[0]["id"]
                collection_ids.append(collection_id)
                created += 1
                print(f"  ✓ '{collection_names[i]}'")

                # Add 2-6 poems to each collection
                selected_poems = random.sample(
                    poem_ids,
                    min(random.randint(2, 6), len(poem_ids))
                )
                for pos, poem_id in enumerate(selected_poems):
                    try:
                        supabase.table("collection_poems").insert({
                            "collection_id": collection_id,
                            "poem_id": poem_id,
                            "position": pos,
                            "added_at": random_date(days_back_min=1, days_back_max=60),
                        }).execute()
                    except Exception:
                        pass
                    time.sleep(0.03)

        except Exception as e:
            print(f"  ✗ Collection error: {e}")

        time.sleep(0.08)

    print(f"\n  → Created {created} collections")


# ── RUN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  PoetryQuill Data Simulator")
    print("  Pseudo-realistic stream generation")
    print("  Based on MS research principles")
    print("="*50)

    start = datetime.now()

    profile_ids = create_profiles(35)

    if not profile_ids:
        print("\n✗ No profiles created. Check your credentials and schema.")
        exit(1)

    poem_ids = create_poems(profile_ids, 55)

    if poem_ids:
        create_likes(profile_ids, poem_ids, 120)
        create_comments(profile_ids, poem_ids, 70)
        create_follows(profile_ids, 80)
        create_collections(profile_ids, poem_ids, 15)

    elapsed = (datetime.now() - start).seconds

    print(f"\n{'='*50}")
    print("  Simulation complete")
    print(f"  Time: {elapsed}s")
    print(f"  Profiles:    35")
    print(f"  Poems:       55")
    print(f"  Likes:       ~120")
    print(f"  Comments:    ~70")
    print(f"  Follows:     ~80")
    print(f"  Collections: 15")
    print("="*50 + "\n")
    