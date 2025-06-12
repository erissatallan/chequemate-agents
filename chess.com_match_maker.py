import cloudscraper
import psycopg2
import psycopg2.extras
import numpy as np
import re
from collections import Counter
from datetime import timezone, datetime

# Active users
USERS = [
    "Whisers1", "PNiskanen", "guessworkceoke",
    "ashot2016", "toshevgeorgi70", "TakeMyCheetos"
]

# Eco codes to track for style vector
ECO_CODES = [f"{c}{i:02d}" for c in "ABCDE" for i in range(100)]  

# Weights for matchmaking (user will tweak later)
WEIGHTS = {
    "w_rating": 0.5,
    "w_streak": 0.2,
    "w_time":   0.2,
    "w_style":  0.1
}


def get_user_matches(username, months=3):
    """
    Fetch up to `months` worth of monthly archives (~90 games).
    """
    scraper = cloudscraper.create_scraper(browser={"custom": "MyApp/1.0"})
    archives = scraper.get(
        f"https://api.chess.com/pub/player/{username}/games/archives"
    ).json().get("archives", [])
    recent = archives[-months:]
    games = []
    for url in recent:
        games.extend(scraper.get(url).json().get("games", []))
    return games  # List of game dicts


def get_current_rating(username, games):
    """
    Take rating from the most recent game for `username`.
    """
    last = games[0]
    me = last["white"] if last["white"]["username"].lower() == username.lower() else last["black"]
    return me["rating"]  # int


def get_streak(username, games, max_checks=10):
    """
    Compute win(+)/loss(-) streak over last up to `max_checks` games.
    """
    streak = 0
    for g in games[:max_checks]:
        me = g["white"] if g["white"]["username"].lower() == username.lower() else g["black"]
        res = me["result"]
        if res == "win":
            streak = streak + 1 if streak >= 0 else 1
        elif res in ("checkmated", "timeout", "resigned"):
            streak = streak - 1 if streak <= 0 else -1
        else:
            break
    return streak  # int


def get_time_preferences(games):
    """
    Returns a dict {time_control: fraction_of_games}.
    """
    cnt = Counter(g["time_control"] for g in games)
    total = sum(cnt.values()) or 1
    return {tc: c/total for tc, c in cnt.items()}


def get_style_vector(games):
    """
    Build normalized frequency vector over tracked ECO_CODES.
    """
    codes = [
        re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1)
        for g in games if "[ECO" in g["pgn"]
    ]
    cnt = Counter(codes)
    vec = np.array([cnt.get(code, 0) for code in ECO_CODES], dtype=float)
    norm = vec.sum() or 1
    return (vec / norm).tolist()  # JSON-serializable list of floats


def persist_features(conn, username, feats):
    """
    Upsert the features for `username` into Postgres.
    Uses INSERT ... ON CONFLICT for atomic insert/update. 
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO player_features
              (username, rating, streak, time_pref, style_vec, last_updated)
            VALUES
              (%s, %s, %s, %s::jsonb, %s::jsonb, NOW())
            ON CONFLICT (username) DO UPDATE
            SET
              rating       = EXCLUDED.rating,
              streak       = EXCLUDED.streak,
              time_pref    = EXCLUDED.time_pref,
              style_vec    = EXCLUDED.style_vec,
              last_updated = NOW();
        """, (
            username,
            feats["rating"],
            feats["streak"],
            psycopg2.extras.Json(feats["time_pref"]),   # auto-serializes to JSONB :contentReference[oaicite:2]{index=2}
            psycopg2.extras.Json(feats["style_vec"])
        ))
    conn.commit()


def load_all_features(conn):
    """
    Load all player_features rows into a dict username→feat_dict.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM player_features;")
        rows = cur.fetchall()
    result = {}
    for r in rows:
        result[r["username"]] = {
            "rating":    r["rating"],
            "streak":    r["streak"],
            "time_pref": r["time_pref"],
            "style_vec": np.array(r["style_vec"], dtype=float)
        }
    return result


def cosine_similarity(a, b):
    """Compute cosine similarity between two numpy arrays."""
    dot = float(np.dot(a, b))
    norm = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return dot / norm


def score_opponent(u_feats, o_feats, w):
    """
    Composite score: rating proximity, streak smoothing, time-control match,
    and style diversity (1 - cosine similarity).
    """
    diff = abs(u_feats["rating"] - o_feats["rating"])
    rating_score = np.exp(- (diff**2) / (2 * (50**2)))  # Gaussian peak :contentReference[oaicite:3]{index=3}
    streak_score = np.exp(-abs(u_feats["streak"]) / 5)
    time_score   = sum(
        u_feats["time_pref"].get(tc, 0) * o_feats["time_pref"].get(tc, 0)
        for tc in u_feats["time_pref"]
    )
    style_score  = 1 - cosine_similarity(u_feats["style_vec"], o_feats["style_vec"])
    return (
        w["w_rating"] * rating_score +
        w["w_streak"] * streak_score +
        w["w_time"]   * time_score +
        w["w_style"]  * style_score
    )


def find_opponent(challenger, all_feats, weights):
    """
    Select the best opponent for `challenger` from `all_feats`.
    """
    u = all_feats[challenger]
    candidates = [
        (name, f) for name, f in all_feats.items()
        if name != challenger
        and abs(f["rating"] - u["rating"]) <= 300
        and any(tc in u["time_pref"] for tc in f["time_pref"])
    ]
    scored = [(score_opponent(u, feat, weights), name) for name, feat in candidates]
    if not scored:
        return None
    scored.sort(reverse=True)
    top_score = scored[0][0]
    top_names = [n for s, n in scored if s == top_score]
    return top_names[0]  # pick the first of ties; you can randomize if you prefer


if __name__ == "__main__":
    # 1) Connect to Postgres
    conn = psycopg2.connect(
        dbname="chequemate",
        user="aerissat",
        password="root",
        host="localhost",
        port=5432
    )

    if conn:
        print("Connected to Postgres")
    else:
        print("Failed to connect to Postgres")
        exit(1)

    # 2) For each active user: fetch games → extract feats → persist
    for user in USERS:
        gs = get_user_matches(user)
        feats = {
            "rating":  get_current_rating(user, gs),
            "streak":  get_streak(user, gs),
            "time_pref": get_time_preferences(gs),
            "style_vec": get_style_vector(gs)
        }
        persist_features(conn, user, feats)

    # 3) Load all features and find a match for one challenger
    features = load_all_features(conn)
    challenger = "guessworkceoke"
    opponent = find_opponent(challenger, features, WEIGHTS)
    print(f"Matched {challenger} → {opponent}")

    conn.close()
