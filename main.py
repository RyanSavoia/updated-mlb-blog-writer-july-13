import os
import random
import json
import re
import time
import hashlib
from datetime import datetime
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from mlb_data_fetcher import MLBDataFetcher

# Configuration from environment variables
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
WEBFLOW_API_TOKEN = os.environ.get('WEBFLOW_API_TOKEN')
WEBFLOW_SITE_ID = os.environ.get('WEBFLOW_SITE_ID')
WEBFLOW_COLLECTION_ID = os.environ.get('WEBFLOW_COLLECTION_ID')

# Validate required environment variables
required_vars = {
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'WEBFLOW_API_TOKEN': WEBFLOW_API_TOKEN,
    'WEBFLOW_SITE_ID': WEBFLOW_SITE_ID,
    'WEBFLOW_COLLECTION_ID': WEBFLOW_COLLECTION_ID
}

for var_name, var_value in required_vars.items():
    if not var_value:
        raise ValueError(f"{var_name} environment variable is required")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Webflow API headers
WEBFLOW_HEADERS = {
    'Authorization': f'Bearer {WEBFLOW_API_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

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

# ==================== WEBFLOW INTEGRATION ====================
def test_webflow_connection():
    """Test Webflow API connection and site access"""
    try:
        # Test site access
        response = requests.get(
            f'https://api.webflow.com/v2/sites/{WEBFLOW_SITE_ID}',
            headers=WEBFLOW_HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            site_data = response.json()
            print(f"✅ Site access verified: {site_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ Site access failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Webflow connection: {e}")
        return False

def create_composite_cover_image(away_team, home_team, away_logo_url, home_logo_url):
    """Create a composite cover image with both team logos"""
    try:
        # Download team logos
        away_response = requests.get(away_logo_url, timeout=10)
        home_response = requests.get(home_logo_url, timeout=10)
        
        away_img = Image.open(BytesIO(away_response.content)).convert('RGBA')
        home_img = Image.open(BytesIO(home_response.content)).convert('RGBA')
        
        # Create canvas (1200x630 for social media)
        canvas = Image.new('RGB', (1200, 630), color='#1a1a1a')
        draw = ImageDraw.Draw(canvas)
        
        # Resize logos to fit nicely
        logo_size = (200, 200)
        away_img = away_img.resize(logo_size, Image.Resampling.LANCZOS)
        home_img = home_img.resize(logo_size, Image.Resampling.LANCZOS)
        
        # Position logos with "VS" between them
        away_x = 250
        home_x = 750
        logo_y = 215
        
        # Paste logos (handle transparency)
        canvas.paste(away_img, (away_x, logo_y), away_img if away_img.mode == 'RGBA' else None)
        canvas.paste(home_img, (home_x, logo_y), home_img if home_img.mode == 'RGBA' else None)
        
        # Add "VS" text
        try:
            # Try to load a font (fallback to default if not available)
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        vs_text = "VS"
        bbox = draw.textbbox((0, 0), vs_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (1200 - text_width) // 2
        text_y = 300
        
        draw.text((text_x, text_y), vs_text, fill='white', font=font)
        
        # Add team names
        try:
            team_font = ImageFont.truetype("arial.ttf", 24)
        except:
            team_font = ImageFont.load_default()
        
        # Away team name
        away_bbox = draw.textbbox((0, 0), away_team, font=team_font)
        away_text_width = away_bbox[2] - away_bbox[0]
        away_text_x = away_x + (200 - away_text_width) // 2
        draw.text((away_text_x, logo_y + 220), away_team, fill='white', font=team_font)
        
        # Home team name
        home_bbox = draw.textbbox((0, 0), home_team, font=team_font)
        home_text_width = home_bbox[2] - home_bbox[0]
        home_text_x = home_x + (200 - home_text_width) // 2
        draw.text((home_text_x, logo_y + 220), home_team, fill='white', font=team_font)
        
        # Add title
        title = f"{away_team} vs {home_team} - MLB Preview"
        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
        except:
            title_font = ImageFont.load_default()
        
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1200 - title_width) // 2
        draw.text((title_x, 100), title, fill='white', font=title_font)
        
        # Save to BytesIO for upload
        img_buffer = BytesIO()
        canvas.save(img_buffer, format='PNG', quality=95)
        img_buffer.seek(0)
        
        return img_buffer
        
    except Exception as e:
        print(f"❌ Error creating composite image: {e}")
        # Fallback: just download one logo
        try:
            response = requests.get(away_logo_url, timeout=10)
            return BytesIO(response.content)
        except:
            return None

def upload_image_to_webflow(image_buffer, filename):
    """Upload image to Webflow assets using the two-step process"""
    import hashlib
    
    try:
        # Step 1: Calculate MD5 hash
        image_buffer.seek(0)
        file_content = image_buffer.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        image_buffer.seek(0)
        
        # Step 2: Create asset metadata to get upload URL
        metadata_payload = {
            "fileName": filename,
            "fileHash": file_hash,
            "originUrl": None
        }
        
        response = requests.post(
            f'https://api.webflow.com/v2/sites/{WEBFLOW_SITE_ID}/assets',
            headers=WEBFLOW_HEADERS,
            json=metadata_payload,
            timeout=30
        )
        
        if response.status_code != 201:
            print(f"❌ Failed to create asset metadata: {response.status_code} - {response.text}")
            return None
        
        asset_data = response.json()
        upload_url = asset_data.get('uploadUrl')
        upload_details = asset_data.get('uploadDetails', {})
        
        if not upload_url:
            print("❌ No upload URL returned from Webflow")
            return None
        
        # Step 3: Upload file to S3 using the provided URL and details
        upload_headers = {}
        files = {'file': (filename, image_buffer, 'image/png')}
        
        # Add any required fields from upload_details
        upload_data = upload_details.copy() if upload_details else {}
        
        s3_response = requests.post(
            upload_url,
            headers=upload_headers,
            files=files,
            data=upload_data,
            timeout=60
        )
        
        if s3_response.status_code in [200, 201, 204]:
            print(f"  ✅ Successfully uploaded to S3")
            # Return the asset URL from the original response
            return asset_data.get('url') or asset_data.get('publicUrl') or f"https://uploads-ssl.webflow.com/{file_hash}/{filename}"
        else:
            print(f"❌ Failed to upload to S3: {s3_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading image to Webflow: {e}")
        return None

def markdown_to_webflow_rich_text(markdown_content):
    """Convert markdown to Webflow-compatible HTML"""
    # Basic markdown to HTML conversion
    html = markdown_content
    
    # Headers
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Prop alert boxes (blockquotes)
    html = re.sub(r'^> 📢 (.*?)$', r'<div style="background:#f2f2f2; padding:12px; border-left:4px solid #4CAF50; margin:15px 0;"><strong>📢 \1</strong></div>', html, flags=re.MULTILINE)
    html = re.sub(r'^> ⚡ (.*?)$', r'<div style="background:#f2f2f2; padding:12px; border-left:4px solid #FF9800; margin:15px 0;"><strong>⚡ \1</strong></div>', html, flags=re.MULTILINE)
    
    # Bullet points
    html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    html = re.sub(r'</ul>\s*<ul>', '', html)  # Merge consecutive lists
    
    # Paragraphs
    html = re.sub(r'\n\n', '</p><p>', html)
    html = f'<p>{html}</p>'
    
    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    
    return html

def create_webflow_post(game_data, blog_content, cover_image_url):
    """Create a new post in Webflow CMS"""
    try:
        # Extract title from blog content
        lines = blog_content.strip().split('\n')
        title = lines[0].replace('#', '').strip() if lines else f"{game_data['matchup']} Preview"
        
        # Create post summary (first paragraph, max 160 chars)
        summary = ""
        for line in lines[2:]:  # Skip title and date
            if line.strip() and not line.startswith('#') and not line.startswith('*'):
                summary = line.strip()[:157] + "..." if len(line.strip()) > 160 else line.strip()
                break
        
        # Create SEO meta description with keywords
        away_team = game_data.get('away_team', '')
        home_team = game_data.get('home_team', '')
        meta_desc = f"Expert {away_team} vs {home_team} betting preview with pitcher analysis, lineup matchups, and prop recommendations. {datetime.now().strftime('%B %d')} MLB betting insights."
        if len(meta_desc) > 250:
            meta_desc = meta_desc[:247] + "..."
        
        # Convert markdown to Webflow rich text
        rich_text_content = markdown_to_webflow_rich_text(blog_content)
        
        # Prepare Webflow CMS item data
        webflow_data = {
            "isArchived": False,
            "isDraft": False,
            "fieldData": {
                "name": title,
                "post-body": rich_text_content,
                "post-summary": summary,
                "main-image": cover_image_url,
                "url": "https://www.thebettinginsider.com/betting/about",
                "meta-title": title,
                "meta-description": meta_desc
            }
        }
        
        # Create the post
        response = requests.post(
            f'https://api.webflow.com/v2/collections/{WEBFLOW_COLLECTION_ID}/items',
            headers=WEBFLOW_HEADERS,
            json=webflow_data,
            timeout=30
        )
        
        if response.status_code == 202:  # Webflow returns 202 for successful creation
            post_data = response.json()
            print(f"  ✅ Created Webflow post: {title}")
            return post_data
        else:
            print(f"  ❌ Failed to create Webflow post: {response.status_code}")
            print(f"     Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating Webflow post: {e}")
        return None

def publish_webflow_site():
    """Publish the Webflow site to make posts live"""
    try:
        response = requests.post(
            f'https://api.webflow.com/v2/sites/{WEBFLOW_SITE_ID}/publish',
            headers=WEBFLOW_HEADERS,
            json={"domains": ["thebettinginsider.com"]},
            timeout=30
        )
        
        if response.status_code == 202:
            print("  ✅ Site published successfully")
            return True
        else:
            print(f"  ❌ Failed to publish site: {response.status_code}")
            print(f"     Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error publishing Webflow site: {e}")
        return False

# ==================== INTERLINKING LOGIC ====================
INTERLINK_MAP = {
    # Stats product
    "betting splits": "https://www.thebettinginsider.com/stats-about",
    "public money": "https://www.thebettinginsider.com/stats-about",
    "betting percentage": "https://www.thebettinginsider.com/stats-about",
    "sharp money": "https://www.thebettinginsider.com/stats-about",
    "betting trends": "https://www.thebettinginsider.com/stats-about",
    "stats dashboard": "https://www.thebettinginsider.com/stats-about",
    # Pitcher arsenal tool
    "pitcher arsenal data": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "pitch mix": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "arsenal-specific performance": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "batter vs pitch type stats": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "projected xBA": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "expected batting average": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "contact-adjusted xBA": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "xBA vs arsenal": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "strikeout percentage": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "K-rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "strikeout rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "whiff rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "swing and miss %": "https://www.thebettinginsider.com/daily-mlb-game-stats"
}

def auto_link_blog_content(blog_text, max_links=5):
    """Automatically insert internal links into blog content"""
    if not blog_text or max_links <= 0:
        return blog_text
    
    links_inserted = 0
    modified_text = blog_text
    
    # Sort phrases by length (longest first) to avoid partial matching issues
    sorted_phrases = sorted(INTERLINK_MAP.keys(), key=len, reverse=True)
    
    for phrase in sorted_phrases:
        if links_inserted >= max_links:
            break
            
        url = INTERLINK_MAP[phrase]
        
        # Create regex pattern for whole word/phrase matching (case-insensitive)
        pattern = r'\b' + re.escape(phrase) + r'\b'
        
        # Check if this phrase exists in the text and isn't already linked
        match = re.search(pattern, modified_text, re.IGNORECASE)
        if match:
            # Check if the matched phrase is already inside a markdown link
            matched_text = match.group()
            start_pos = match.start()
            
            # Look backwards from match to see if we're inside a link
            preceding_text = modified_text[:start_pos]
            last_link_start = preceding_text.rfind('[')
            last_link_end = preceding_text.rfind(')')
            
            # If we're inside a link, skip this phrase
            if last_link_start > last_link_end and '](' in modified_text[last_link_start:start_pos + len(matched_text) + 10]:
                continue
            
            # Replace only the first occurrence with a markdown link
            link_markdown = f'[{matched_text}]({url})'
            modified_text = re.sub(pattern, link_markdown, modified_text, count=1, flags=re.IGNORECASE)
            links_inserted += 1
            
            print(f"  🔗 Added internal link: '{matched_text}' -> {url}")
    
    if links_inserted > 0:
        print(f"  ✅ Total internal links added: {links_inserted}")
    
    return modified_text

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
    """Generate MLB blog prompt with randomized headers and SEO enhancements"""
    
    headers = get_blog_headers()
    
    # Create shorter, more SEO-friendly title
    if ' at ' in topic:
        teams = topic.replace(' MLB Betting Preview', '').split(' at ')
        seo_title = f"{teams[0]} vs {teams[1]}: Betting Preview & Props ({datetime.now().strftime('%b %d')})"
    else:
        seo_title = topic.replace('MLB Betting Preview', 'Odds, Props & Analysis')
    
    prompt = f"""You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 500–800 word blog post that follows this EXACT structure:

# {seo_title}
*Last updated: {datetime.now().strftime('%B %d, %Y')}*

**Game Time:** [time from game_time field]

## {headers['intro']}
Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section.

## {headers['pitchers']}
**Pitching Matchup:** [Away Pitcher] vs [Home Pitcher]

### [Away Pitcher Name] ([Away Team]):
List ALL pitch types with EXACT usage percentages and velocities from away_pitcher.arsenal.
Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"
Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)
How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"

### [Home Pitcher Name] ([Home Team]):
Same detailed structure: List ALL pitches with exact usage % and mph from home_pitcher.arsenal
"The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"

## {headers['lineups']}
**Lineup Matchups & Batting Edges**

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
**Strikeout Risks & Rewards**
For each team:
Use away_arsenal_k_pct vs away_season_k_pct and home_arsenal_k_pct vs home_season_k_pct.
Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."
Interpretation: Higher = potential K prop value, Lower = potential contact play

## {headers['umpire']}
**Behind the Plate:** [Umpire Name]
If umpire field is NOT "TBA" and umpire data exists:
Show exact umpire name from umpire field
Convert umpire_k_boost from multiplier to percentage: 1.11x = "+11% strikeouts"
Convert umpire_bb_boost from multiplier to percentage: 1.03x = "+3% walks"
IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly
Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"
If umpire field is "TBA" or missing:
"Umpire assignment has not been announced, which makes prop volatility a concern."

## {headers['lean']}
**Final Lean & Betting Takeaway**

STEP-BY-STEP BETTING ANALYSIS:

STEP 1: Check ALL individual batters for prop opportunities
Go through every batter in away_key_performers and home_key_performers
BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020
If ANY batter meets BOTH criteria, create a prop alert like this:
> 📢 **Prop Alert**: [Player Name] (.XXX → .XXX, +XX points) meets betting lean criteria!

STEP 2: Check team strikeout rates for pitcher props
Check away_arsenal_k_pct vs away_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
Check home_arsenal_k_pct vs home_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
If criteria met, create strikeout alert:
> ⚡ **K Prop Alert**: [Pitcher Name] strikeout OVER - [Team]'s K-rate jumps to XX.X% vs this arsenal!

STEP 3: Report findings
If NO criteria met: "No significant statistical edges meet our betting threshold in this matchup."

## 🔑 Key Takeaways
Create 3-4 bullet points summarizing the main insights:
- Key player advantages/disadvantages
- Pitcher prop opportunities (or lack thereof)
- Umpire impact assessment
- Overall betting recommendation

## 🧠 FAQs

**Q: Who is the best betting prop for the [Away Team] vs [Home Team] game?**
A: [Answer based on your analysis - mention specific player if criteria met, or "No players meet our strict betting criteria" if none qualify]

**Q: Is [Umpire Name] a pitcher-friendly umpire?**
A: [Answer based on umpire data - "Slightly pitcher-friendly with +X% strikeouts" or "Mixed tendencies" or "TBA" if unknown]

**Q: What time is the [Away Team] vs [Home Team] game?**
A: [Game time from game_time field]

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
11. NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points
12. NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%
13. Use the prop alert boxes (>) for any qualifying recommendations
14. OUTPUT MUST BE VALID MARKDOWN - USE # ## ### HEADERS, NOT HTML

Blog Title: {seo_title}
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
                "content": "You are a professional MLB betting analyst and blog writer who specializes in pitcher-batter matchups and umpire analysis. Write engaging, data-driven content for baseball fans and bettors. Always output in clean Markdown format with SEO enhancements."
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

# ==================== MAIN BLOG GENERATION LOGIC ====================
def generate_and_publish_daily_blogs():
    """Generate all blogs for today and publish to Webflow"""
    print(f"🚀 Starting daily blog generation and Webflow publishing at {datetime.now()}")
    
    mlb_fetcher = MLBDataFetcher()
    blog_topics = mlb_fetcher.get_blog_topics_from_games()
    
    if not blog_topics:
        print("❌ No games available for blog generation")
        return
    
    print(f"🔄 Found {len(blog_topics)} games for today")
    
    successful_posts = 0
    
    for i, blog_topic in enumerate(blog_topics, 1):
        topic = blog_topic['topic']
        keywords = blog_topic['keywords']
        game_data = blog_topic['game_data']
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']}")
        
        try:
            # Generate blog post with SEO enhancements
            print("  🤖 Generating blog post with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            print(f"  ✅ Generated blog post ({len(blog_post)} characters)")
            
            # Add internal links
            print("  🔗 Adding internal links...")
            blog_post_with_links = auto_link_blog_content(blog_post)
            print("  ✅ Internal links added")
            
            # Create composite cover image with fallback
            print("  🖼️ Creating composite cover image...")
            away_team = game_data['away_team']
            home_team = game_data['home_team']
            away_logo_url = get_team_logo_url(away_team)
            home_logo_url = get_team_logo_url(home_team)
            
            cover_image_url = None
            
            try:
                # Try to create and upload composite image first
                cover_image_buffer = create_composite_cover_image(
                    away_team, home_team, away_logo_url, home_logo_url
                )
                
                if cover_image_buffer:
                    print("  ☁️ Uploading composite image to Webflow...")
                    cover_filename = f"{away_team.lower()}-vs-{home_team.lower()}-{datetime.now().strftime('%Y%m%d')}.png"
                    
                    start_time = time.time()
                    cover_image_url = upload_image_to_webflow(cover_image_buffer, cover_filename)
                    upload_time = time.time() - start_time
                    
                    if cover_image_url:
                        print(f"  ✅ Composite image uploaded in {upload_time:.1f}s")
                    else:
                        print(f"  ⚠️ Composite upload failed after {upload_time:.1f}s")
                
                # Fallback: Use direct ESPN logo URL if composite failed
                if not cover_image_url:
                    print("  🔄 Fallback: Using home team logo directly...")
                    cover_image_url = home_logo_url  # Use home team logo as fallback
                    print(f"  ✅ Using fallback image: {cover_image_url}")
                    
            except Exception as e:
                print(f"  ⚠️ Image processing error: {e}")
                # Fallback to direct logo URL
                cover_image_url = home_logo_url
                print(f"  ✅ Using fallback image: {cover_image_url}")
            
            # Webflow requires a cover image, so we must have one
            if not cover_image_url:
                print("  ❌ No cover image available - skipping this post")
                continue
            
            # Create Webflow CMS post (cover image is required)
            print("  📤 Creating Webflow CMS post...")
            webflow_post = create_webflow_post(game_data, blog_post_with_links, cover_image_url)
            
            if webflow_post:
                successful_posts += 1
                print(f"  ✅ Successfully published to Webflow")
            else:
                print(f"  ❌ Failed to create Webflow post")
            
            # Small delay between posts to avoid rate limits
            time.sleep(1)
            
            # Small delay between posts to avoid rate limits
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    # Publish the site to make all posts live
    if successful_posts > 0:
        print(f"\n🌐 Publishing Webflow site with {successful_posts} new posts...")
        if publish_webflow_site():
            print(f"🎉 Successfully published {successful_posts} blog posts to Webflow!")
        else:
            print(f"⚠️ Posts created but site publish failed - check Webflow dashboard")
    else:
        print("❌ No posts were successfully created")

if __name__ == '__main__':
    print("🏟️ MLB Blog Generator - Webflow Edition")
    
    # Test Webflow connection first
    print("🔗 Testing Webflow API connection...")
    if not test_webflow_connection():
        print("❌ Webflow connection failed. Check your Site ID and API token.")
        print(f"   Site ID: {WEBFLOW_SITE_ID}")
        print(f"   Token starts with: {WEBFLOW_API_TOKEN[:20]}...")
        exit(1)
    
    print("🔄 Generating and publishing blogs...")
    generate_and_publish_daily_blogs()
    print("✅ Blog generation complete!")
