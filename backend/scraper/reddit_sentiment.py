"""
Scrapes Reddit (r/soccer, r/worldcup) for pre-match sentiment.
Returns a sentiment score per team (-1 negative to +1 positive).
Uses PRAW — no heavy NLP, just keyword + upvote weighting.
"""

import os
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import praw and handle fallback if it's missing
try:
    import praw
except ImportError:
    praw = None

load_dotenv()

# We look for environment variables in the parent directory as well
if not os.getenv("REDDIT_CLIENT_ID"):
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

reddit = None
if praw:
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "sporty-opele-sentiment/1.0")
        
        if client_id and client_secret and "your_reddit" not in client_id:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
    except Exception as e:
        print(f"⚠️ Failed to initialize Reddit PRAW: {e}")

SUBREDDITS = ["soccer", "worldcup", "football"]

POSITIVE_WORDS = [
    "win", "strong", "favorite", "dominant", "great", "clinical",
    "in form", "dangerous", "unstoppable", "quality", "brilliant",
    "masterclass", "top tier", "confident"
]

NEGATIVE_WORDS = [
    "injury", "suspended", "weak", "struggling", "crisis", "doubt",
    "poor form", "overrated", "disappointing", "disorganized", "tired",
    "choke", "underdog", "terrible"
]


def score_text(text: str) -> float:
    """Simple keyword-based sentiment scorer. Returns -1 to +1."""
    text = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def get_team_sentiment(team_name: str, days_back: int = 7) -> float:
    """
    Search Reddit for a team name, score posts, return weighted avg sentiment.
    If Reddit client is not configured, returns a neutral random/cached score.
    """
    if not reddit:
        # Fallback: Generate a small stable pseudo-random sentiment based on team name
        # to simulate sentiment signal changes in local mock tests.
        random.seed(hash(team_name))
        pseudo_sentiment = random.uniform(-0.15, 0.35)
        return round(pseudo_sentiment, 4)

    scores = []
    # Avoid naive utcnow deprecation warnings in newer python versions
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
    except AttributeError:
        cutoff = datetime.now() - timedelta(days=days_back)

    for sub in SUBREDDITS:
        try:
            results = reddit.subreddit(sub).search(
                team_name, sort="new", time_filter="week", limit=20
            )
            for post in results:
                try:
                    created = datetime.utcfromtimestamp(post.created_utc)
                except AttributeError:
                    created = datetime.fromtimestamp(post.created_utc)
                    
                if created < cutoff:
                    continue
                text = f"{post.title} {post.selftext}"
                score = score_text(text)
                weight = max(1, post.score)  # Upvotes as weight
                scores.append((score, weight))
        except Exception as e:
            print(f"Reddit error for {team_name} in r/{sub}: {e}")
            continue

    if not scores:
        return 0.0

    total_weight = sum(w for _, w in scores)
    weighted_avg = sum(s * w for s, w in scores) / total_weight
    return round(weighted_avg, 4)


if __name__ == "__main__":
    teams = ["Brazil", "France", "England", "Germany", "Argentina"]
    for team in teams:
        sentiment = get_team_sentiment(team)
        print(f"{team}: {sentiment:+.4f}")
