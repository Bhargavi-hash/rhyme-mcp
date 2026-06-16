# server.py — PoetryQuill Analytics MCP Server
# Connects Claude Desktop to your live Supabase database
# Ask Claude natural language questions about your platform data

import os
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

server = Server("poetryquill-analytics")


# ── TOOL DEFINITIONS ─────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [

        types.Tool(
            name="get_platform_overview",
            description=(
                "Get a high-level overview of PoetryQuill — "
                "total users, poems, likes, comments, and recent growth. "
                "Use this first to understand the platform's overall health."
            ),
            inputSchema={"type": "object", "properties": {}}
        ),

        types.Tool(
            name="get_top_poems",
            description=(
                "Get the most popular poems on PoetryQuill ranked by likes or views. "
                "Returns title, author_id, like_count, view_count, comment_count, tags, and published date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many poems to return (default 10, max 25)",
                        "default": 10
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Sort by 'like_count', 'view_count', or 'comment_count'",
                        "enum": ["like_count", "view_count", "comment_count"],
                        "default": "like_count"
                    }
                }
            }
        ),

        types.Tool(
            name="get_top_authors",
            description=(
                "Get the most active or most followed authors on PoetryQuill. "
                "Returns username, display_name, poem_count, follower_count, points, streak, country."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many authors to return (default 10)",
                        "default": 10
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Sort by 'poem_count', 'follower_count', or 'points'",
                        "enum": ["poem_count", "follower_count", "points"],
                        "default": "follower_count"
                    }
                }
            }
        ),

        types.Tool(
            name="get_engagement_trends",
            description=(
                "Analyze engagement trends over a time window — "
                "new poems published, likes given, comments written, new users joined. "
                "Good for spotting growth patterns or activity spikes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 30)",
                        "default": 30
                    }
                }
            }
        ),

        types.Tool(
            name="get_content_sample",
            description=(
                "Retrieve a sample of recent published poems for Claude to analyze. "
                "Use this to identify writing themes, tag patterns, content trends, "
                "or generate insights about what's being written on the platform."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of poems to sample (default 15, max 30)",
                        "default": 15
                    },
                    "order": {
                        "type": "string",
                        "description": "Get 'recent' poems or 'popular' poems",
                        "enum": ["recent", "popular"],
                        "default": "recent"
                    }
                }
            }
        ),

        types.Tool(
            name="get_user_growth",
            description=(
                "Analyze user signup trends over time. "
                "Returns signup counts broken into time buckets to show growth curve."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Total days to analyze (default 90)",
                        "default": 90
                    }
                }
            }
        ),

        types.Tool(
            name="get_tag_analytics",
            description=(
                "Analyze which tags are most used across poems. "
                "Reveals what themes and topics writers are exploring most on the platform."
            ),
            inputSchema={"type": "object", "properties": {}}
        ),

        types.Tool(
            name="get_streak_leaderboard",
            description=(
                "Get users with the highest current writing streaks and longest historical streaks. "
                "Shows platform engagement and habit formation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many users to return (default 10)",
                        "default": 10
                    }
                }
            }
        ),

        types.Tool(
            name="get_collections_overview",
            description=(
                "Get an overview of public collections on the platform — "
                "how many exist, which have the most poems, curation patterns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many collections to return (default 10)",
                        "default": 10
                    }
                }
            }
        ),

        types.Tool(
            name="get_geographic_distribution",
            description=(
                "See where PoetryQuill users are from. "
                "Returns country distribution across the user base."
            ),
            inputSchema={"type": "object", "properties": {}}
        ),

    ]


# ── TOOL HANDLERS ─────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    def respond(data):
        return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

    def error(msg):
        return [types.TextContent(type="text", text=f"Error: {msg}")]

    try:

        # ── Platform Overview ──
        if name == "get_platform_overview":
            total_users = supabase.table("profiles").select("*", count="exact").execute()
            total_poems = supabase.table("poems").select("*", count="exact").filter("is_published", "eq", True).execute()
            total_likes = supabase.table("likes").select("*", count="exact").execute()
            total_comments = supabase.table("comments").select("*", count="exact").execute()
            total_collections = supabase.table("collections").select("*", count="exact").execute()
            total_follows = supabase.table("follows").select("*", count="exact").execute()

            # Growth in last 30 days
            cutoff_30 = (datetime.now() - timedelta(days=30)).isoformat()
            new_users_30 = supabase.table("profiles").select("*", count="exact").gte("created_at", cutoff_30).execute()
            new_poems_30 = supabase.table("poems").select("*", count="exact").gte("created_at", cutoff_30).filter("is_published", "eq", True).execute()

            return respond({
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
                    "avg_comments_per_poem": round(total_comments.count / max(total_poems.count, 1), 2),
                }
            })

        # ── Top Poems ──
        elif name == "get_top_poems":
            limit = min(arguments.get("limit", 10), 25)
            order_by = arguments.get("order_by", "like_count")

            poems = supabase.table("poems").select(
                "id, title, author_id, like_count, view_count, comment_count, tags, published_at, created_at"
            ).filter("is_published", "eq", True).order(order_by, desc=True).limit(limit).execute()

            return respond({
                "ordered_by": order_by,
                "count": len(poems.data),
                "poems": poems.data
            })

        # ── Top Authors ──
        elif name == "get_top_authors":
            limit = min(arguments.get("limit", 10), 25)
            order_by = arguments.get("order_by", "follower_count")

            authors = supabase.table("profiles").select(
                "username, display_name, poem_count, follower_count, following_count, points, current_streak, longest_streak, country, created_at"
            ).order(order_by, desc=True).limit(limit).execute()

            return respond({
                "ordered_by": order_by,
                "count": len(authors.data),
                "authors": authors.data
            })

        # ── Engagement Trends ──
        elif name == "get_engagement_trends":
            days = arguments.get("days", 30)
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            new_poems = supabase.table("poems").select("*", count="exact").gte("created_at", cutoff).filter("is_published", "eq", True).execute()
            new_likes = supabase.table("likes").select("*", count="exact").gte("created_at", cutoff).execute()
            new_comments = supabase.table("comments").select("*", count="exact").gte("created_at", cutoff).execute()
            new_users = supabase.table("profiles").select("*", count="exact").gte("created_at", cutoff).execute()
            new_follows = supabase.table("follows").select("*", count="exact").gte("created_at", cutoff).execute()

            return respond({
                "period_days": days,
                "new_poems": new_poems.count,
                "new_likes": new_likes.count,
                "new_comments": new_comments.count,
                "new_users": new_users.count,
                "new_follows": new_follows.count,
                "daily_averages": {
                    "poems_per_day": round(new_poems.count / days, 2),
                    "likes_per_day": round(new_likes.count / days, 2),
                    "comments_per_day": round(new_comments.count / days, 2),
                }
            })

        # ── Content Sample ──
        elif name == "get_content_sample":
            limit = min(arguments.get("limit", 15), 30)
            order = arguments.get("order", "recent")

            order_col = "created_at" if order == "recent" else "like_count"

            poems = supabase.table("poems").select(
                "title, content, tags, like_count, view_count, comment_count, published_at"
            ).filter("is_published", "eq", True).order(order_col, desc=True).limit(limit).execute()

            return respond({
                "sample_type": order,
                "count": len(poems.data),
                "poems": poems.data,
                "instruction": "Analyze these poems for themes, writing styles, tag patterns, and platform content trends."
            })

        # ── User Growth ──
        elif name == "get_user_growth":
            days = arguments.get("days", 90)

            # Break into weekly buckets
            buckets = []
            for week in range(days // 7):
                week_end = datetime.now() - timedelta(days=week * 7)
                week_start = week_end - timedelta(days=7)

                count = supabase.table("profiles").select(
                    "*", count="exact"
                ).gte("created_at", week_start.isoformat()).lt("created_at", week_end.isoformat()).execute()

                buckets.append({
                    "week_ending": week_end.strftime("%Y-%m-%d"),
                    "new_users": count.count
                })

            buckets.reverse()  # chronological order

            return respond({
                "period_days": days,
                "weekly_signups": buckets,
                "total_in_period": sum(b["new_users"] for b in buckets)
            })

        # ── Tag Analytics ──
        elif name == "get_tag_analytics":
            poems = supabase.table("poems").select(
                "tags, like_count"
            ).filter("is_published", "eq", True).execute()

            tag_counts = {}
            tag_likes = {}

            for poem in poems.data:
                tags = poem.get("tags", []) or []
                likes = poem.get("like_count", 0)
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    tag_likes[tag] = tag_likes.get(tag, 0) + likes

            sorted_by_count = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            sorted_by_likes = sorted(tag_likes.items(), key=lambda x: x[1], reverse=True)

            return respond({
                "unique_tags": len(tag_counts),
                "poems_with_tags": sum(1 for p in poems.data if p.get("tags")),
                "top_tags_by_usage": [{"tag": t, "poem_count": c} for t, c in sorted_by_count[:15]],
                "top_tags_by_likes": [{"tag": t, "total_likes": l} for t, l in sorted_by_likes[:15]],
            })

        # ── Streak Leaderboard ──
        elif name == "get_streak_leaderboard":
            limit = min(arguments.get("limit", 10), 25)

            current = supabase.table("profiles").select(
                "username, display_name, current_streak, longest_streak, poem_count, points"
            ).order("current_streak", desc=True).limit(limit).execute()

            longest = supabase.table("profiles").select(
                "username, display_name, current_streak, longest_streak, poem_count"
            ).order("longest_streak", desc=True).limit(limit).execute()

            return respond({
                "top_current_streaks": current.data,
                "top_longest_streaks": longest.data,
            })

        # ── Collections Overview ──
        elif name == "get_collections_overview":
            limit = min(arguments.get("limit", 10), 25)

            collections = supabase.table("collections").select(
                "name, description, poem_count, is_public, created_at"
            ).filter("is_public", "eq", True).order("poem_count", desc=True).limit(limit).execute()

            total = supabase.table("collections").select("*", count="exact").execute()
            public = supabase.table("collections").select("*", count="exact").filter("is_public", "eq", True).execute()

            return respond({
                "total_collections": total.count,
                "public_collections": public.count,
                "private_collections": total.count - public.count,
                "top_collections_by_size": collections.data
            })

        # ── Geographic Distribution ──
        elif name == "get_geographic_distribution":
            users = supabase.table("profiles").select("country").execute()

            country_counts = {}
            for user in users.data:
                country = user.get("country") or "global"
                country_counts[country] = country_counts.get(country, 0) + 1

            sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)

            return respond({
                "total_users": len(users.data),
                "countries_represented": len(country_counts),
                "distribution": [{"country": c, "users": n} for c, n in sorted_countries]
            })

        else:
            return error(f"Unknown tool: {name}")

    except Exception as e:
        return error(str(e))


# ── ENTRY POINT ───────────────────────────────────────────────

async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

    