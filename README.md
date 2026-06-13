# Rhyme Analytics MCP

An MCP server that connects Claude Desktop to Rhyme's live Supabase database.
Ask Claude natural language questions about your platform data.

## Setup

### 1. Install dependencies
```pip install mcp supabase python-dotenv```

### 2. Configure credentials
```cp .env.example .env```
# Edit .env and add your Supabase URL and service role key

### 3. Run the simulator (optional — adds realistic demo data)
```python simulate.py```

### 4. Connect to Claude Desktop
Add to ~/.config/Claude/claude_desktop_config.json:
```
{
  "mcpServers": {
    "poetryquill": {
      "command": "python",
      "args": ["/full/path/to/server.py"]
    }
  }
}
```
### 5. Restart Claude Desktop
Look for the hammer icon — your tools are connected.

## Example questions to ask Claude

- "Give me a platform overview of PoetryQuill"
- "What are the top 10 most liked poems?"
- "Who are the most followed authors?"
- "Analyze engagement trends over the last 30 days"
- "What tags are writers using most?"
- "Show me the user growth over the last 90 days"
- "Which collections have the most poems?"
- "Analyze a sample of recent poems and tell me what themes are trending"
- "Who has the longest writing streak?"
- "Where are our users from?"

## Tools available

| Tool | What it does |
|------|-------------|
| get_platform_overview | Totals, ratios, 30-day growth |
| get_top_poems | Most liked/viewed/commented poems |
| get_top_authors | Most followed/active/points authors |
| get_engagement_trends | Activity over a time window |
| get_content_sample | Poems for Claude to analyze themes |
| get_user_growth | Weekly signup trends |
| get_tag_analytics | Tag usage and engagement by tag |
| get_streak_leaderboard | Current and longest writing streaks |
| get_collections_overview | Public collections and sizes |
| get_geographic_distribution | Where users are from |

## Schema
Built for Rhyme's Supabase schema:
profiles, poems, likes, comments, follows, collections, collection_poems

