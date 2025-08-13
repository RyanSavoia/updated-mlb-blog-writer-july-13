import os
import threading
import time
import schedule
import random
import json
import re
from datetime import datetime
from urllib.parse import quote
from flask import Flask, Response, render_template, redirect, url_for
from openai import OpenAI
from mlb_data_fetcher import MLBDataFetcher

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# ==================== MLB TEAM LOGOS ====================
TEAM_LOGOS = {
    'NYY': 'nyy', 'Yankees': 'nyy',
    'TOR': 'tor', 'Blue Jays': 'tor',
    'BOS': 'bos', 'Red Sox': 'bos',
    'LAD': 'lad', 'Dodgers': 'lad',
    'SF': 'sf', 'Giants': 'sf',
    'HOU': 'hou', 'Astros': 'hou',
    'ATL': 'atl', 'Braves': 'atl',
    'NYM': 'nym', 'Mets': 'nym',
    'PHI': 'phi', 'Phillies': 'phi',
    'WSN': 'wsh', 'Nationals': 'wsh',
    'MIA': 'mia', 'Marlins': 'mia',
    'CHC': 'chc', 'Cubs': 'chc',
    'MIL': 'mil', 'Brewers': 'mil',
    'STL': 'stl', 'Cardinals': 'stl',
    'CIN': 'cin', 'Reds': 'cin',
    'PIT': 'pit', 'Pirates': 'pit',
    'LAA': 'laa', 'Angels': 'laa',
    'SEA': 'sea', 'Mariners': 'sea',
    'TEX': 'tex', 'Rangers': 'tex',
    'OAK': 'oak', 'Athletics': 'oak',
    'MIN': 'min', 'Twins': 'min',
    'CWS': 'chw', 'White Sox': 'chw',
    'CLE': 'cle', 'Guardians': 'cle',
    'DET': 'det', 'Tigers': 'det',
    'KC': 'kc', 'Royals': 'kc',
    'TB': 'tb', 'Rays': 'tb',
    'BAL': 'bal', 'Orioles': 'bal',
    'COL': 'col', 'Rockies': 'col',
    'ARI': 'ari', 'Diamondbacks': 'ari',
    'SD': 'sd', 'Padres': 'sd'
}

def get_team_logo_url(team_name):
    """Get official team logo URL from ESPN"""
    team_clean = team_name.strip().upper()
    
    team_mappings = {
        'YANKEES': 'nyy', 'NEW YORK YANKEES': 'nyy',
        'BLUE JAYS': 'tor', 'TORONTO BLUE JAYS': 'tor', 'TORONTO': 'tor',
        'RED SOX': 'bos', 'BOSTON RED SOX': 'bos', 'BOSTON': 'bos',
        'DODGERS': 'lad', 'LOS ANGELES DODGERS': 'lad',
        'GIANTS': 'sf', 'SAN FRANCISCO GIANTS': 'sf',
        'ASTROS': 'hou', 'HOUSTON ASTROS': 'hou',
        'BRAVES': 'atl', 'ATLANTA BRAVES': 'atl',
        'METS': 'nym', 'NEW YORK METS': 'nym',
        'PHILLIES': 'phi', 'PHILADELPHIA PHILLIES': 'phi',
        'NATIONALS': 'wsh', 'WASHINGTON NATIONALS': 'wsh',
        'MARLINS': 'mia', 'MIAMI MARLINS': 'mia',
        'CUBS': 'chc', 'CHICAGO CUBS': 'chc',
        'BREWERS': 'mil', 'MILWAUKEE BREWERS': 'mil',
        'CARDINALS': 'stl', 'ST LOUIS CARDINALS': 'stl',
        'REDS': 'cin', 'CINCINNATI REDS': 'cin',
        'PIRATES': 'pit', 'PITTSBURGH PIRATES': 'pit',
        'ANGELS': 'laa', 'LOS ANGELES ANGELS': 'laa',
        'MARINERS': 'sea', 'SEATTLE MARINERS': 'sea',
        'RANGERS': 'tex', 'TEXAS RANGERS': 'tex',
        'ATHLETICS': 'oak', 'OAKLAND ATHLETICS': 'oak',
        'TWINS': 'min', 'MINNESOTA TWINS': 'min',
        'WHITE SOX': 'chw', 'CHICAGO WHITE SOX': 'chw',
        'GUARDIANS': 'cle', 'CLEVELAND GUARDIANS': 'cle',
        'TIGERS': 'det', 'DETROIT TIGERS': 'det',
        'ROYALS': 'kc', 'KANSAS CITY ROYALS': 'kc',
        'RAYS': 'tb', 'TAMPA BAY RAYS': 'tb',
        'ORIOLES': 'bal', 'BALTIMORE ORIOLES': 'bal',
        'ROCKIES': 'col', 'COLORADO ROCKIES': 'col',
        'DIAMONDBACKS': 'ari', 'ARIZONA DIAMONDBACKS': 'ari',
        'PADRES': 'sd', 'SAN DIEGO PADRES': 'sd'
    }
    
    # Try exact match first
    if team_clean in TEAM_LOGOS:
        team_code = TEAM_LOGOS[team_clean]
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code}.png"
    
    # Try team name mappings
    if team_clean in team_mappings:
        team_code = team_mappings[team_clean]
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code}.png"
    
    # Try partial matches
    for key, code in TEAM_LOGOS.items():
        if key in team_clean or team_clean in key:
            return f"https://a.espncdn.com/i/teamlogos/mlb/500/{code}.png"
    
    for name, code in team_mappings.items():
        if name in team_clean or team_clean in name:
            return f"https://a.espncdn.com/i/teamlogos/mlb/500/{code}.png"
    
    print(f"⚠️  No logo match found for: {team_name}")
    return "https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png"

def generate_team_logos_for_matchup(away_team, home_team):
    """Generate both team logos for a matchup"""
    away_logo = get_team_logo_url(away_team)
    home_logo = get_team_logo_url(home_team)
    
    return {
        'away_team': away_team,
        'away_logo': away_logo,
        'home_team': home_team,
        'home_logo': home_logo,
        'combined_url': f"Matchup: {away_team} ({away_logo}) @ {home_team} ({home_logo})"
    }

# ==================== BLOG PROMPTS ====================
def get_blog_headers():
    """Generate randomized headers to avoid scaled content detection"""
    return {
        "intro": random.choice([
            "Brief Intro", 
            "Game Overview", 
            "Matchup Setup",
            "Today's Setup",
            "Game Preview"
        ]),
        "pitchers": random.choice([
            "Pitcher Breakdown", 
            "Rotation Report", 
            "Starting Pitching Analysis",
            "Mound Matchup",
            "Pitching Preview"
        ]),
        "lineups": random.choice([
            "Lineup Matchups", 
            "Batting Edges vs Arsenal", 
            "Offensive Breakdown",
            "Lineup Advantage vs Arsenal",
            "Hitting Matchups"
        ]),
        "strikeouts": random.choice([
            "Strikeout Trends", 
            "K-Risk Analysis", 
            "Whiff Outlook",
            "Lineup Strikeout Trends vs Arsenal",
            "Contact vs Strikeout Profile"
        ]),
        "umpire": random.choice([
            "Umpire Impact", 
            "Behind the Plate", 
            "Umpire Trends",
            "Umpire Influence",
            "Plate Umpire Analysis"
        ]),
        "lean": random.choice([
            "Final Lean & Takeaway", 
            "Betting Breakdown", 
            "Where the Edge Is",
            "Betting Interpretation / Final Lean",
            "Our Betting Take"
        ])
    }

def get_mlb_blog_post_prompt(topic, keywords, game_data):
    """Generate MLB blog prompt with randomized headers"""
    
    headers = get_blog_headers()
    
    prompt = f"""You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure:

# {topic}
Game Time: [time from game_time field]

## {headers['intro']}
Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section.

## {headers['pitchers']}
Pitching Matchup: [Away Pitcher] vs [Home Pitcher]

### [Away Pitcher Name] ([Away Team]):
List ALL pitch types with EXACT usage percentages and velocities from away_pitcher.arsenal.
Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"
Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)
How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"

### [Home Pitcher Name] ([Home Team]):
Same detailed structure: List ALL pitches with exact usage % and mph from home_pitcher.arsenal
"The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"

## {headers['lineups']}
Lineup Matchups & Batting Edges

For Away Team vs Home Pitcher:
Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"
From away_key_performers, show:
The batter with the BIGGEST INCREASE in xBA (if any)
The batter with the BIGGEST DECREASE in xBA (if any)
Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)
Skip batters with minimal changes (under 15 point differences)

For Home Team vs Away Pitcher:
Same detailed structure using home_key_performers.
Focus on biggest increase and biggest decrease only.

## {headers['strikeouts']}
Strikeout Risks & Rewards
For each team:
Use away_arsenal_k_pct vs away_season_k_pct and home_arsenal_k_pct vs home_season_k_pct.
Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."
Interpretation: Higher = potential K prop value, Lower = potential contact play

## {headers['umpire']}
Behind the Plate: [Umpire Name]
If umpire field is NOT "TBA" and umpire data exists:
Show exact umpire name from umpire field
Convert umpire_k_boost from multiplier to percentage: 1.11x = "+11% strikeouts"
Convert umpire_bb_boost from multiplier to percentage: 1.03x = "+3% walks"
IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly
Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"
If umpire field is "TBA" or missing:
"Umpire assignment has not been announced, which makes prop volatility a concern."
CRITICAL: Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.

## {headers['lean']}
Final Lean & Betting Takeaway

STEP-BY-STEP BETTING ANALYSIS:

STEP 1: Check ALL individual batters for prop opportunities
Go through every batter in away_key_performers and home_key_performers
BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020
CRITICAL MATH CHECK - VERIFY THESE NUMBERS:
.272 is LESS THAN .300 = NO LEAN
.278 is LESS THAN .300 = NO LEAN
.299 is LESS THAN .300 = NO LEAN
.301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
.315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
Always verify: Is the xBA number actually above 0.300 before suggesting a lean?
Example: Juan Soto (.263 → .369, +106 points) = LEAN because .369 > .300 AND +106 > +20
Example: Randal Grichuk (.235 → .278, +43 points) = NO LEAN because .278 < .300
Example: Marcell Ozuna (.238 → .272, +34 points) = NO LEAN because .272 < .300

STEP 2: Check team strikeout rates for pitcher props
Check away_arsenal_k_pct vs away_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
Check home_arsenal_k_pct vs home_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
Check for UNDER: If arsenal K% < 15% AND decrease > 4%, lean UNDER
Example: Atlanta 23.4% → 27.6% vs Kikuchi = LEAN OVER because 27.6% > 25% AND +4.2% > +4%

STEP 3: Report findings
IMPORTANT: Only suggest leans for players/props that meet the EXACT criteria above.
If ANY batter meets BOTH criteria (xBA > 0.300 AND boost > +20):
"Our final lean would be on [Player Name] - his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."
If ANY team K% meets criteria (K% > 25% AND increase > 4%):
"Our final lean would be [Pitcher Name] strikeout OVER - [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."
If multiple leans exist, pick the strongest statistical edge.
If NO criteria met:
"No significant statistical edges meet our betting threshold in this matchup."

CRITICAL RULES:
1. Use ONLY the JSON data provided below - NO external stats or guessing
2. If data is missing, say "data not available" rather than inventing
3. Convert all multipliers (1.15x) to percentages (+15%)
4. Focus on the biggest statistical edges from the data
5. Keep tone sharp and analytical, avoid generic phrases
6. ALWAYS include exact pitch usage percentages and velocities from arsenal data
7. Show exact season BA vs projected xBA for all lineup comparisons
8. Only highlight batters with biggest increases AND biggest decreases (skip minimal changes)
9. Apply strict betting criteria - don't suggest weak leans
10. Remember: walks help hitters, strikeouts help pitchers
11. ALWAYS include the game time right after the title
12. ALWAYS include the betting information right after the game time
13. NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points
14. NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%
15. OUTPUT MUST BE VALID MARKDOWN - USE # ## ### HEADERS, NOT HTML

Blog Title: {topic}
Target Keywords: {keywords}

Game Data (JSON):
{game_data}
"""
    
    return prompt

# ==================== BLOG GENERATION ====================
def generate_mlb_blog_post(topic, keywords, game_data):
    """Generate MLB-specific blog post using game data"""
    prompt = get_mlb_blog_post_prompt(topic, keywords, game_data)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a professional MLB betting analyst and blog writer who specializes in pitcher-batter matchups and umpire analysis. Write engaging, data-driven content for baseball fans and bettors. Always output in clean Markdown format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=4096,
        temperature=0.7
    )
    
    return response.choices[0].message.content

# ==================== SEO & UTILITY FUNCTIONS ====================
def save_to_file(directory, filename, content):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def create_slug(matchup, game_time):
    """Create SEO-friendly slug from matchup and time"""
    slug = matchup.lower().replace(' @ ', '-vs-').replace(' ', '-')
    
    if game_time and game_time != 'TBD':
        try:
            if ',' in game_time:
                time_part = game_time.split(',')[1].strip()
            else:
                time_part = game_time.strip()
            time_clean = time_part.lower().replace(':', '').replace(' ', '')
            slug += f"-{time_clean}"
        except:
            pass
    
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def generate_blog_schema(game_data, blog_content, slug, date_str):
    """Generate JSON-LD schema for SEO"""
    
    lines = blog_content.strip().split('\n')
    title = lines[0] if lines else f"{game_data['matchup']} Preview"
    if title.startswith('#'):
        title = title.replace('#', '').strip()
    
    description = ""
    for line in lines[1:]:
        if line.strip() and not line.startswith('#'):
            description = line.strip()[:160]
            break
    
    if not description:
        description = f"MLB game preview: {game_data['matchup']} on {game_data.get('game_date', date_str)}"
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": f"{date_str}T00:00:00Z",
        "dateModified": f"{date_str}T00:00:00Z",
        "author": {
            "@type": "Organization",
            "name": "MLB Blog Generator"
        },
        "publisher": {
            "@type": "Organization",
            "name": "MLB Blog Generator"
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"/mlb-blogs/{date_str}/{slug}"
        },
        "articleSection": "Sports",
        "keywords": f"MLB, {game_data['away_team']}, {game_data['home_team']}, baseball, preview",
        "about": [
            {
                "@type": "SportsTeam",
                "name": game_data['away_team']
            },
            {
                "@type": "SportsTeam", 
                "name": game_data['home_team']
            }
        ]
    }
    
    return schema

def parse_game_time_for_sorting(time_str):
    """Parse game time for proper chronological sorting"""
    if not time_str or time_str == 'TBD':
        return 9999
    
    try:
        if ',' in time_str:
            time_part = time_str.split(',')[1].strip()
        else:
            time_part = time_str.strip()
        
        if 'PM' in time_part:
            hour = int(time_part.split(':')[0])
            if hour != 12:
                hour += 12
            minute = int(time_part.split(':')[1].replace('PM', ''))
        else:
            hour = int(time_part.split(':')[0])
            if hour == 12:
                hour = 0
            minute = int(time_part.split(':')[1].replace('AM', ''))
        
        return hour * 100 + minute
    except Exception as e:
        print(f"⚠️ Error parsing time '{time_str}': {e}")
        return 9999

# ==================== MAIN BLOG GENERATION LOGIC ====================
def generate_daily_blogs():
    """Generate all blogs for today with SEO metadata"""
    print(f"🚀 Starting daily blog generation at {datetime.now()}")
    
    mlb_fetcher = MLBDataFetcher()
    blog_topics = mlb_fetcher.get_blog_topics_from_games()
    
    if not blog_topics:
        print("❌ No games available for blog generation")
        return
    
    print(f"🔄 Sorting {len(blog_topics)} games by time...")
    blog_topics.sort(key=lambda x: parse_game_time_for_sorting(x['game_data'].get('game_time', 'TBD')))
    
    for i, topic in enumerate(blog_topics):
        game_time = topic['game_data'].get('game_time', 'TBD')
        print(f"  {i+1}. {topic['topic']} - {game_time}")
    
    base_directory = "mlb_blog_posts"
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_directory = os.path.join(base_directory, date_str)
    
    if not os.path.exists(daily_directory):
        os.makedirs(daily_directory)
    
    print(f"🚀 Generating {len(blog_topics)} MLB blog posts for {date_str}")
    
    blog_index = []
    
    for i, blog_topic in enumerate(blog_topics, 1):
        topic = blog_topic['topic']
        keywords = blog_topic['keywords']
        game_data = blog_topic['game_data']
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']} at {game_data.get('game_time', 'TBD')}")
        
        slug = create_slug(game_data['matchup'], game_data.get('game_time'))
        game_directory = os.path.join(daily_directory, slug)
        
        try:
            print("  🤖 Generating blog post with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "blog_post.md", blog_post)
            print(f"  ✅ Generated blog post ({len(blog_post)} characters)")
            
            print("  🏆 Getting team logos...")
            away_team = game_data['away_team']
            home_team = game_data['home_team']
            team_logos = generate_team_logos_for_matchup(away_team, home_team)
            
            logo_info = f"""Away Team: {team_logos['away_team']}
Away Logo: {team_logos['away_logo']}
Home Team: {team_logos['home_team']}
Home Logo: {team_logos['home_logo']}"""
            
            save_to_file(game_directory, "team_logos.txt", logo_info)
            print(f"  ✅ Team logos saved: {away_team} & {home_team}")
            
            print("  🔍 Generating SEO schema...")
            schema = generate_blog_schema(game_data, blog_post, slug, date_str)
            save_to_file(game_directory, "schema.json", json.dumps(schema, indent=2))
            print("  ✅ SEO schema saved")
            
            meta = {
                "slug": slug,
                "title": schema["headline"],
                "description": schema["description"],
                "matchup": game_data['matchup'],
                "game_time": game_data.get('game_time', 'TBD'),
                "away_team": game_data['away_team'],
                "home_team": game_data['home_team'],
                "away_logo": team_logos['away_logo'],
                "home_logo": team_logos['home_logo'],
                "url": f"/mlb-blogs/{date_str}/{slug}",
                "generated_at": datetime.now().isoformat()
            }
            
            save_to_file(game_directory, "meta.json", json.dumps(meta, indent=2))
            blog_index.append(meta)
            print("  ✅ Blog metadata saved")
            
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            print("  ✅ Game data saved")
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    save_to_file(daily_directory, "index.json", json.dumps({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "total_blogs": len(blog_index),
        "blogs": blog_index
    }, indent=2))
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts in {daily_directory}")

# ==================== FLASK ROUTES ====================
@app.route('/')
def home():
    """Redirect to today's blog index"""
    today = datetime.now().strftime("%Y-%m-%d")
    return redirect(url_for('blog_index', date=today))

@app.route('/mlb-blogs/<date>')
def blog_index(date):
    """Display index of all blogs for a specific date"""
    blog_dir = f"mlb_blog_posts/{date}"
    index_file = os.path.join(blog_dir, "index.json")
    
    if not os.path.exists(index_file):
        return f"""
        <html>
        <head><title>No Blogs Found - {date}</title></head>
        <body>
            <h1>No blogs found for {date}</h1>
            <p>Blogs may still be generating...</p>
            <p><a href="/generate">Trigger manual generation</a></p>
        </body>
        </html>
        """, 404
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB Blog Posts - {date}</title>
        <meta name="description" content="Daily MLB game previews and analysis for {date}. {index_data['total_blogs']} games covered.">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .game-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .game-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
            .game-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .matchup {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .game-time {{ color: #666; margin-bottom: 10px; }}
            .teams {{ display: flex; align-items: center; gap: 10px; margin: 10px 0; }}
            .team-logo {{ width: 30px; height: 30px; }}
            .description {{ color: #555; line-height: 1.5; }}
            .read-more {{ display: inline-block; margin-top: 10px; color: #007bff; text-decoration: none; }}
            .read-more:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏟️ MLB Blog Posts - {date}</h1>
            <p>📊 {index_data['total_blogs']} games • 🕐 Generated at {index_data['generated_at'][:19].replace('T', ' ')}</p>
        </div>
        <div class="game-grid">
    """
    
    for blog in index_data['blogs']:
        html += f"""
            <div class="game-card">
                <div class="matchup">{blog['matchup']}</div>
                <div class="game-time">⏰ {blog['game_time']}</div>
                <div class="teams">
                    <img src="{blog['away_logo']}" alt="{blog['away_team']}" class="team-logo" onerror="this.style.display='none'">
                    <span>vs</span>
                    <img src="{blog['home_logo']}" alt="{blog['home_team']}" class="team-logo" onerror="this.style.display='none'">
                </div>
                <div class="description">{blog['description']}</div>
                <a href="{blog['url']}" class="read-more">Read Full Preview →</a>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/mlb-blogs/<date>/<slug>')
def show_blog(date, slug):
    """Display individual blog post with SEO schema"""
    folder_path = f"mlb_blog_posts/{date}/{slug}"
    file_path = os.path.join(folder_path, "blog_post.md")
    schema_path = os.path.join(folder_path, "schema.json")
    meta_path = os.path.join(folder_path, "meta.json")
    
    if not os.path.exists(file_path):
        return "<h1>Blog not found</h1>", 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        blog_content = f.read()
    
    schema = {}
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    # Convert markdown to HTML (basic conversion)
    html_content = blog_content.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_content = f"<p>{html_content}</p>"
    
    # Handle headers
    html_content = re.sub(r'<p># (.*?)</p>', r'<h1>\1</h1>', html_content)
    html_content = re.sub(r'<p>## (.*?)</p>', r'<h2>\1</h2>', html_content)
    html_content = re.sub(r'<p>### (.*?)</p>', r'<h3>\1</h3>', html_content)
    
    title = schema.get('headline', meta.get('title', f"MLB: {meta.get('matchup', 'Game Preview')}"))
    description = schema.get('description', meta.get('description', ''))
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <meta name="description" content="{description}">
        <link rel="canonical" href="/mlb-blogs/{date}/{slug}">
        <style>
            body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .meta {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .teams {{ display: flex; align-items: center; gap: 15px; margin: 20px 0; }}
            .team {{ display: flex; align-items: center; gap: 10px; }}
            .team-logo {{ width: 40px; height: 40px; }}
            .back-link {{ margin: 20px 0; }}
            .back-link a {{ color: #3498db; text-decoration: none; }}
            .back-link a:hover {{ text-decoration: underline; }}
        </style>
        <script type="application/ld+json">
        {json.dumps(schema, indent=2) if schema else '{}'}
        </script>
    </head>
    <body>
        <div class="back-link">
            <a href="/mlb-blogs/{date}">← Back to {date} Games</a>
        </div>
        
        <div class="meta">
            <div class="teams">
                <div class="team">
                    <img src="{meta.get('away_logo', '')}" alt="{meta.get('away_team', '')}" class="team-logo" onerror="this.style.display='none'">
                    <strong>{meta.get('away_team', '')}</strong>
                </div>
                <span>@</span>
                <div class="team">
                    <img src="{meta.get('home_logo', '')}" alt="{meta.get('home_team', '')}" class="team-logo" onerror="this.style.display='none'">
                    <strong>{meta.get('home_team', '')}</strong>
                </div>
            </div>
            <div>🕐 Game Time: {meta.get('game_time', 'TBD')}</div>
        </div>
        
        <article>
            {html_content}
        </article>
        
        <div class="back-link">
            <a href="/mlb-blogs/{date}">← Back to {date} Games</a>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/generate')
def manual_generate():
    """Manual trigger to generate blogs"""
    generate_daily_blogs()
    return "Blog generation triggered! Check back in a few minutes."

@app.route('/health')
def health():
    """Health check"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

# ==================== SCHEDULER ====================
def run_scheduler():
    """Run daily blog generation at 7 AM EDT"""
    schedule.every().day.at("11:00").do(generate_daily_blogs)  # 11:00 UTC = 7:00 AM EDT
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def initialize_app():
    """Initialize with Flask server first, then generate blogs in background"""
    print("🚀 Initializing MLB Blog Service")
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Background scheduler started - will generate daily at 7 AM EDT")
    
    def delayed_blog_generation():
        time.sleep(5)
        generate_daily_blogs()
    
    blog_thread = threading.Thread(target=delayed_blog_generation, daemon=True)
    blog_thread.start()
    print("✅ Blog generation started in background")

if __name__ == '__main__':
    initialize_app()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
