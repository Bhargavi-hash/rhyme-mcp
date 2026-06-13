# app.py — Web interface for PoetryQuill Analytics
# Runs a local web server you open in your browser
# No Claude Desktop needed

import os
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import anthropic
from supabase import create_client, Client
import uvicorn

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

anthropic_client = anthropic.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

app = FastAPI()


# ── DATABASE FUNCTIONS ───────────────────────────────────────
# Same logic as server.py but called directly

def get_platform_overview():
    total_users = supabase.table("profiles").select("*", count="exact").execute()
    total_poems = supabase.table("poems").select("*", count="exact").filter("is_published", "eq", True).execute()
    total_likes = supabase.table("likes").select("*", count="exact").execute()
    total_comments = supabase.table("comments").select("*", count="exact").execute()
    total_collections = supabase.table("collections").select("*", count="exact").execute()
    total_follows = supabase.table("follows").select("*", count="exact").execute()

    cutoff_30 = (datetime.now() - timedelta(days=30)).isoformat()
    new_users_30 = supabase.table("profiles").select("*", count="exact").gte("created_at", cutoff_30).execute()
    new_poems_30 = supabase.table("poems").select("*", count="exact").gte("created_at", cutoff_30).filter("is_published", "eq", True).execute()

    return {
        "platform": "PoetryQuill",
        "totals": {
            "users": total_users.count,
            "published_poems": total_poems.count,
            "likes": total_likes.count,
            "comments": total_comments.count,
            "collections": total_collections.count,
            "follows": total_follows.count,
        },
        "last_30_days": {
            "new_users": new_users_30.count,
            "new_poems": new_poems_30.count,
        },
        "ratios": {
            "avg_poems_per_user": round(total_poems.count / max(total_users.count, 1), 2),
            "avg_likes_per_poem": round(total_likes.count / max(total_poems.count, 1), 2),
        }
    }


def get_top_poems(limit=10, order_by="like_count"):
    poems = supabase.table("poems").select(
        "id, title, author_id, like_count, view_count, comment_count, tags, published_at"
    ).filter("is_published", "eq", True).order(order_by, desc=True).limit(limit).execute()
    return {"ordered_by": order_by, "poems": poems.data}


def get_top_authors(limit=10, order_by="follower_count"):
    authors = supabase.table("profiles").select(
        "username, display_name, poem_count, follower_count, points, current_streak, country"
    ).order(order_by, desc=True).limit(limit).execute()
    return {"ordered_by": order_by, "authors": authors.data}


def get_engagement_trends(days=30):
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    new_poems = supabase.table("poems").select("*", count="exact").gte("created_at", cutoff).filter("is_published", "eq", True).execute()
    new_likes = supabase.table("likes").select("*", count="exact").gte("created_at", cutoff).execute()
    new_comments = supabase.table("comments").select("*", count="exact").gte("created_at", cutoff).execute()
    new_users = supabase.table("profiles").select("*", count="exact").gte("created_at", cutoff).execute()
    return {
        "period_days": days,
        "new_poems": new_poems.count,
        "new_likes": new_likes.count,
        "new_comments": new_comments.count,
        "new_users": new_users.count,
        "daily_averages": {
            "poems_per_day": round(new_poems.count / days, 2),
            "likes_per_day": round(new_likes.count / days, 2),
        }
    }


def get_tag_analytics():
    poems = supabase.table("poems").select("tags, like_count").filter("is_published", "eq", True).execute()
    tag_counts = {}
    for poem in poems.data:
        for tag in (poem.get("tags") or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return {"top_tags": [{"tag": t, "count": c} for t, c in sorted_tags[:15]]}


def get_streak_leaderboard(limit=10):
    data = supabase.table("profiles").select(
        "username, display_name, current_streak, longest_streak, poem_count"
    ).order("current_streak", desc=True).limit(limit).execute()
    return {"leaderboard": data.data}


def get_content_sample(limit=15):
    poems = supabase.table("poems").select(
        "title, content, tags, like_count, view_count"
    ).filter("is_published", "eq", True).order("like_count", desc=True).limit(limit).execute()
    return {"poems": poems.data}


def get_geographic_distribution():
    users = supabase.table("profiles").select("country").execute()
    country_counts = {}
    for user in users.data:
        country = user.get("country") or "global"
        country_counts[country] = country_counts.get(country, 0) + 1
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    return {"distribution": [{"country": c, "users": n} for c, n in sorted_countries]}


# ── TOOL REGISTRY ────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_platform_overview",
        "description": "Get overall PoetryQuill stats — users, poems, likes, comments, growth",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_top_poems",
        "description": "Get most popular poems by likes, views, or comments",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "order_by": {"type": "string", "enum": ["like_count", "view_count", "comment_count"], "default": "like_count"}
            }
        }
    },
    {
        "name": "get_top_authors",
        "description": "Get most followed or most active authors",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "order_by": {"type": "string", "enum": ["follower_count", "poem_count", "points"], "default": "follower_count"}
            }
        }
    },
    {
        "name": "get_engagement_trends",
        "description": "Analyze engagement over a time window",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30}
            }
        }
    },
    {
        "name": "get_tag_analytics",
        "description": "See which tags writers use most",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_streak_leaderboard",
        "description": "Get users with highest writing streaks",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10}
            }
        }
    },
    {
        "name": "get_content_sample",
        "description": "Sample recent poems for theme and trend analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 15}
            }
        }
    },
    {
        "name": "get_geographic_distribution",
        "description": "See where PoetryQuill users are from",
        "input_schema": {"type": "object", "properties": {}}
    },
]


def call_tool(name, args):
    """Call the right function based on tool name."""
    if name == "get_platform_overview":
        return get_platform_overview()
    elif name == "get_top_poems":
        return get_top_poems(**args)
    elif name == "get_top_authors":
        return get_top_authors(**args)
    elif name == "get_engagement_trends":
        return get_engagement_trends(**args)
    elif name == "get_tag_analytics":
        return get_tag_analytics()
    elif name == "get_streak_leaderboard":
        return get_streak_leaderboard(**args)
    elif name == "get_content_sample":
        return get_content_sample(**args)
    elif name == "get_geographic_distribution":
        return get_geographic_distribution()
    return {"error": f"Unknown tool: {name}"}


# ── API ENDPOINT ─────────────────────────────────────────────

class Query(BaseModel):
    question: str


@app.post("/ask")
async def ask(query: Query):
    """Send question to Claude, let it call tools, return answer."""

    messages = [{"role": "user", "content": query.question}]

    # Agentic loop — Claude calls tools until it has enough data
    while True:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=(
                "You are an analytics assistant for PoetryQuill, a poetry writing platform. "
                "Use the available tools to answer questions about the platform's data. "
                "Always use tools to get real data rather than guessing. "
                "Present insights clearly and highlight interesting patterns."
            ),
            tools=TOOLS,
            messages=messages
        )

        # If Claude is done — return the response
        if response.stop_reason == "end_turn":
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "No response generated."
            )
            return {"answer": text}

        # If Claude wants to use tools
        if response.stop_reason == "tool_use":
            # Add Claude's response to message history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Call each tool Claude requested
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str)
                    })

            # Add tool results to message history
            messages.append({
                "role": "user",
                "content": tool_results
            })

        else:
            break

    return {"answer": "Something went wrong."}


# ── WEB UI ───────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PoetryQuill Analytics</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0A0F1E;
    color: #F0EDE6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 3rem 1.5rem;
  }
  .header { text-align: center; margin-bottom: 2.5rem; }
  .header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #00D4B4;
    margin-bottom: 0.5rem;
  }
  .header p { color: rgba(240,237,230,0.5); font-size: 0.9rem; }
  .chat-box {
    width: 100%;
    max-width: 760px;
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    overflow: hidden;
  }
  .messages {
    padding: 1.5rem;
    min-height: 400px;
    max-height: 560px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .message {
    padding: 0.875rem 1.125rem;
    border-radius: 8px;
    font-size: 0.9rem;
    line-height: 1.7;
    max-width: 88%;
    white-space: pre-wrap;
  }
  .message.user {
    background: rgba(0,212,180,0.12);
    border: 1px solid rgba(0,212,180,0.2);
    color: #F0EDE6;
    align-self: flex-end;
  }
  .message.assistant {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    color: #F0EDE6;
    align-self: flex-start;
  }
  .message.thinking {
    color: rgba(240,237,230,0.4);
    font-style: italic;
    font-size: 0.82rem;
    background: none;
    border: none;
    padding: 0.25rem 0;
  }
  .input-row {
    display: flex;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    background: #0d1425;
  }
  input {
    flex: 1;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    color: #F0EDE6;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s;
  }
  input:focus { border-color: rgba(0,212,180,0.4); }
  input::placeholder { color: rgba(240,237,230,0.3); }
  button {
    background: #00D4B4;
    color: #0A0F1E;
    border: none;
    border-radius: 6px;
    padding: 0.75rem 1.25rem;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: opacity 0.2s;
    white-space: nowrap;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .suggestions {
    width: 100%;
    max-width: 760px;
    margin-top: 1.25rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .suggestion {
    font-size: 0.78rem;
    padding: 0.4rem 0.875rem;
    border-radius: 20px;
    border: 1px solid rgba(0,212,180,0.25);
    color: rgba(0,212,180,0.8);
    background: rgba(0,212,180,0.06);
    cursor: pointer;
    transition: all 0.15s;
  }
  .suggestion:hover {
    background: rgba(0,212,180,0.12);
    border-color: rgba(0,212,180,0.5);
  }
</style>
</head>
<body>

<div class="header">
  <h1>PoetryQuill Analytics</h1>
  <p>Ask Claude anything about your platform data</p>
</div>

<div class="chat-box">
  <div class="messages" id="messages">
    <div class="message assistant">
      Hi! I'm connected to PoetryQuill's live database.
      Ask me anything about your platform — users, poems, engagement trends, 
      popular content, writing streaks, or geographic distribution.
    </div>
  </div>
  <div class="input-row">
    <input
      type="text"
      id="input"
      placeholder="Ask about your platform..."
      onkeydown="if(event.key==='Enter') ask()"
    />
    <button onclick="ask()" id="btn">Ask Claude</button>
  </div>
</div>

<div class="suggestions">
  <span class="suggestion" onclick="fill('Give me a full platform overview')">Platform overview</span>
  <span class="suggestion" onclick="fill('What are the top 10 most liked poems?')">Top poems</span>
  <span class="suggestion" onclick="fill('Who are the most followed authors?')">Top authors</span>
  <span class="suggestion" onclick="fill('Analyze engagement trends over the last 30 days')">Engagement trends</span>
  <span class="suggestion" onclick="fill('What tags are writers using most?')">Tag analytics</span>
  <span class="suggestion" onclick="fill('Who has the longest writing streak?')">Streak leaderboard</span>
  <span class="suggestion" onclick="fill('Where are our users from?')">User geography</span>
  <span class="suggestion" onclick="fill('Analyze recent poems and tell me what themes are trending')">Content themes</span>
</div>

<script>
function fill(text) {
  document.getElementById('input').value = text;
  document.getElementById('input').focus();
}

function addMessage(text, role) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

async function ask() {
  const input = document.getElementById('input');
  const btn = document.getElementById('btn');
  const question = input.value.trim();
  if (!question) return;

  addMessage(question, 'user');
  input.value = '';
  btn.disabled = true;

  const thinking = addMessage('Claude is querying your database...', 'thinking');

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    const data = await res.json();
    thinking.remove();
    addMessage(data.answer, 'assistant');
  } catch (err) {
    thinking.remove();
    addMessage('Error connecting to server. Is it running?', 'thinking');
  }

  btn.disabled = false;
  input.focus();
}
</script>

</body>
</html>
"""


# ── RUN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
