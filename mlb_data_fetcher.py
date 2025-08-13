# mlb_data_fetcher.py
import requests
import json
from datetime import datetime

class MLBDataFetcher:
    def __init__(self):
        self.mlb_api_url = "https://mlb-matchup-api-savant.onrender.com/latest"
        self.umpire_api_url = "https://umpire-json-api.onrender.com"
        self.betting_api_url = "https://draftkings-splits-scraper-webservice.onrender.com/mlb"
    
    def get_mlb_data(self):
        """Fetch MLB matchup data"""
        try:
            print("🌐 Fetching MLB data...")
            response = requests.get(self.mlb_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got {len(data.get('reports', []))} games")
            return data.get('reports', [])
        except Exception as e:
            print(f"❌ Error fetching MLB data: {e}")
            return []

    def get_umpire_data(self):
        """Fetch umpire data"""
        try:
            print("🌐 Fetching umpire data...")
            response = requests.get(self.umpire_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got umpire data for {len(data)} umpires")
            return data
        except Exception as e:
            print(f"❌ Error fetching umpire data: {e}")
            return []

    def get_betting_data(self):
        """Fetch betting odds and splits data"""
        try:
            print("🌐 Fetching betting data...")
            response = requests.get(self.betting_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got betting data for {len(data.get('games', []))} games")
            return data.get('games', [])
        except Exception as e:
            print(f"❌ Error fetching betting data: {e}")
            return []

    def find_game_umpire(self, umpires, matchup):
        """Find the umpire for a specific game matchup"""
        for ump in umpires:
            if ump.get('matchup', '-') == matchup:
                return ump
        
        if ' @ ' in matchup:
            away_team, home_team = matchup.split(' @ ')
            for ump in umpires:
                ump_matchup = ump.get('matchup', '-')
                if away_team in ump_matchup and home_team in ump_matchup:
                    return ump
        
        return None

    def find_game_betting_data(self, betting_games, matchup):
        """Find betting data for a specific game matchup with better team matching"""
        if ' @ ' not in matchup:
            return None
            
        away_team, home_team = matchup.split(' @ ')
        
        print(f"🔍 Looking for betting data: {away_team} @ {home_team}")
        
        # Enhanced team mapping for better matching
        team_mapping = {
            # MLB API code -> DraftKings full name patterns
            'LAA': ['LA Angels', 'LAA Angels', 'Angels'],
            'LAD': ['LA Dodgers', 'LAD Dodgers', 'Dodgers'],
            'NYM': ['NY Mets', 'NYM Mets', 'Mets'],
            'NYY': ['NY Yankees', 'NYY Yankees', 'Yankees'],
            'CWS': ['CHI White Sox', 'CWS White Sox', 'White Sox'],
            'CHC': ['CHI Cubs', 'CHC Cubs', 'Cubs'],
            'TB': ['TB Rays', 'Rays'],
            'SF': ['SF Giants', 'Giants'],
            'SD': ['SD Padres', 'Padres'],
            'KC': ['KC Royals', 'Royals'],
            'WSH': ['WAS Mystics', 'WSH Nationals', 'Nationals'],  # Handle both
            'ARI': ['ARI Diamondbacks', 'AZ Diamondbacks', 'Diamondbacks'],
            'AZ': ['ARI Diamondbacks', 'AZ Diamondbacks', 'Diamondbacks'],
            'MIA': ['MIA Marlins', 'Marlins'],
            'CIN': ['CIN Reds', 'Reds'],
            'COL': ['COL Rockies', 'Rockies'],
            'BOS': ['BOS Red Sox', 'Red Sox'],
            'MIL': ['MIL Brewers', 'Brewers'],
            'PIT': ['PIT Pirates', 'Pirates'],
            'HOU': ['HOU Astros', 'Astros'],
            'CLE': ['CLE Guardians', 'Guardians'],
            'TEX': ['TEX Rangers', 'Rangers'],
            'DET': ['DET Tigers', 'Tigers'],
            'MIN': ['MIN Twins', 'Twins'],
            'TOR': ['TOR Blue Jays', 'Blue Jays'],
            'ATL': ['ATL Braves', 'Braves'],
            'BAL': ['BAL Orioles', 'Orioles'],
            'PHI': ['PHI Phillies', 'Phillies'],
            'SEA': ['SEA Mariners', 'Mariners'],
            'STL': ['STL Cardinals', 'Cardinals'],
            'ATH': ['Athletics'],
        }
        
        def get_team_matches(team_code):
            """Get all possible team name matches for a team code"""
            if team_code in team_mapping:
                return team_mapping[team_code]
            return [team_code]  # Fallback to original code
        
        away_matches = get_team_matches(away_team)
        home_matches = get_team_matches(home_team)
        
        # Find matching betting game
        for game in betting_games:
            betting_away = game.get('away_team', '')
            betting_home = game.get('home_team', '')
            
            print(f"  🔍 Checking: {betting_away} @ {betting_home}")
            
            # Check if any of the away team matches work
            away_match = any(match in betting_away for match in away_matches)
            home_match = any(match in betting_home for match in home_matches)
            
            if away_match and home_match:
                print(f"  ✅ Found match: {betting_away} @ {betting_home}")
                return game
        
        print(f"  ❌ No betting data found for {away_team} @ {home_team}")
        return None

    def format_pitcher_arsenal(self, pitcher_data):
        """Format pitcher arsenal for blog content"""
        arsenal = pitcher_data.get('arsenal', {})
        if not arsenal:
            return "Mixed arsenal"
        
        sorted_pitches = sorted(arsenal.items(), key=lambda x: x[1]['usage_rate'], reverse=True)
        arsenal_text = []
        
        for pitch_type, pitch_data in sorted_pitches:
            pitch_name = pitch_data.get('name', pitch_type)
            usage = pitch_data['usage_rate'] * 100
            speed = pitch_data['avg_speed']
            arsenal_text.append(f"{pitch_name} ({usage:.0f}% usage, {speed:.1f} mph)")
        
        return "; ".join(arsenal_text)

    def calculate_lineup_advantage(self, key_matchups, pitcher_name):
        """Calculate comprehensive lineup stats vs specific pitcher including K% data"""
        pitcher_matchups = [m for m in key_matchups if m.get('vs_pitcher') == pitcher_name]
        reliable_matchups = [m for m in pitcher_matchups if m.get('reliability', '').upper() in ['MEDIUM', 'HIGH']]
        
        if not reliable_matchups:
            return {
                'ba_advantage': 0.0,
                'k_advantage': 0.0,
                'season_ba': 0.250,
                'arsenal_ba': 0.250,
                'season_k_pct': 22.5,
                'arsenal_k_pct': 22.5,
                'top_performers': []
            }
        
        season_bas = []
        season_k_pcts = []
        arsenal_bas = []
        arsenal_k_pcts = []
        top_performers = []
        
        for matchup in reliable_matchups:
            baseline = matchup.get('baseline_stats', {})
            if baseline:
                season_ba = baseline.get('season_avg', 0.250)
                season_k = baseline.get('season_k_pct', 22.5)
                season_bas.append(season_ba)
                season_k_pcts.append(season_k)
            else:
                season_ba = 0.250
                season_k = 22.5
            
            arsenal_ba = matchup.get('weighted_est_ba', 0.250)
            arsenal_k = matchup.get('weighted_k_rate', 22.5)
            arsenal_bas.append(arsenal_ba)
            arsenal_k_pcts.append(arsenal_k)
            
            # Calculate advantages
            ba_diff = arsenal_ba - season_ba
            k_diff = arsenal_k - season_k  # Positive = more strikeouts (bad for batter)
            
            # Track significant performers (20+ point BA difference OR 3%+ K difference)
            if abs(ba_diff) > 0.020 or abs(k_diff) > 3.0:
                batter = matchup.get('batter', 'Unknown')
                batter_name = batter.replace(', ', ' ').split()
                batter_display = f"{batter_name[1]} {batter_name[0]}" if len(batter_name) >= 2 else batter
                
                # Determine advantage type
                if ba_diff > 0.020:
                    advantage = 'strong_ba'  # Good batting average advantage
                elif ba_diff < -0.020:
                    advantage = 'poor_ba'   # Poor batting average matchup
                elif k_diff < -3.0:
                    advantage = 'low_k'     # Less likely to strike out
                elif k_diff > 3.0:
                    advantage = 'high_k'    # More likely to strike out
                else:
                    advantage = 'moderate'
                
                top_performers.append({
                    'name': batter_display,
                    'season_ba': season_ba,
                    'arsenal_ba': arsenal_ba,
                    'season_k': season_k,
                    'arsenal_k': arsenal_k,
                    'ba_diff': ba_diff,
                    'k_diff': k_diff,
                    'advantage': advantage
                })
        
        # Calculate team averages
        avg_season_ba = sum(season_bas) / len(season_bas) if season_bas else 0.250
        avg_season_k = sum(season_k_pcts) / len(season_k_pcts) if season_k_pcts else 22.5
        avg_arsenal_ba = sum(arsenal_bas) / len(arsenal_bas)
        avg_arsenal_k = sum(arsenal_k_pcts) / len(arsenal_k_pcts)
        
        return {
            'ba_advantage': avg_arsenal_ba - avg_season_ba,
            'k_advantage': avg_arsenal_k - avg_season_k,  # Positive = more Ks (bad for lineup)
            'season_ba': avg_season_ba,
            'arsenal_ba': avg_arsenal_ba,
            'season_k_pct': avg_season_k,
            'arsenal_k_pct': avg_arsenal_k,
            'top_performers': top_performers
        }

    def format_betting_info(self, betting_game):
        """Format betting odds and splits into a readable sentence"""
        if not betting_game or 'markets' not in betting_game:
            return "Betting odds not available for this game."
        
        moneyline = betting_game['markets'].get('Moneyline', [])
        if not moneyline or len(moneyline) < 2:
            return "Betting odds not available for this game."
        
        # Find favorite and underdog
        favorite = None
        underdog = None
        
        for team_bet in moneyline:
            odds = team_bet.get('odds', '+100')
            if odds.startswith('−') or odds.startswith('-'):  # Favorite
                favorite = team_bet
            else:  # Underdog
                underdog = team_bet
        
        if not favorite or not underdog:
            return "Betting odds not available for this game."
        
        # Determine which team has more money (higher handle%)
        fav_handle = int(favorite['handle_pct'].replace('%', ''))
        und_handle = int(underdog['handle_pct'].replace('%', ''))
        
        if fav_handle > und_handle:
            money_team = favorite['team']
            money_pct = favorite['handle_pct']
        else:
            money_team = underdog['team']
            money_pct = underdog['handle_pct']
        
        # Format the sentence
        fav_team = favorite['team']
        fav_odds = favorite['odds']
        und_team = underdog['team']
        und_odds = underdog['odds']
        
        return f"DraftKings has {fav_team} as a {fav_odds} favorite and {und_team} as a {und_odds} underdog, with {money_pct} of the money backing {money_team}."

    def parse_game_time_for_sorting(self, time_str):
        """Parse game time for proper chronological sorting"""
        if not time_str or time_str == 'TBD':
            return 9999  # Sort TBD games to the end
        
        try:
            # Handle format like "7/8, 06:40PM" or just "06:40PM"
            if ',' in time_str:
                time_part = time_str.split(',')[1].strip()
            else:
                time_part = time_str.strip()
            
            # Convert to 24-hour format for proper sorting
            if 'PM' in time_part:
                hour = int(time_part.split(':')[0])
                if hour != 12:
                    hour += 12
                minute = int(time_part.split(':')[1].replace('PM', ''))
            else:  # AM
                hour = int(time_part.split(':')[0])
                if hour == 12:
                    hour = 0
                minute = int(time_part.split(':')[1].replace('AM', ''))
            
            return hour * 100 + minute  # Returns like 1840 for 6:40PM
        except Exception as e:
            print(f"⚠️ Error parsing time '{time_str}': {e}")
            return 9999  # Sort unparseable times to end

    def get_blog_topics_from_games(self):
        """Generate blog topics from current MLB games"""
        mlb_reports = self.get_mlb_data()
        umpires = self.get_umpire_data()
        betting_games = self.get_betting_data()
        
        if not mlb_reports:
            return []
        
        blog_topics = []
        
        for game_report in mlb_reports:
            try:
                matchup = game_report.get('matchup', 'Unknown')
                if ' @ ' not in matchup:
                    continue
                    
                away_team, home_team = matchup.split(' @ ')
                
                # Get pitcher data
                away_pitcher_data = game_report['pitchers']['away']
                home_pitcher_data = game_report['pitchers']['home']
                
                # Format pitcher names
                away_pitcher_name = away_pitcher_data.get('name', 'Unknown').replace(', ', ' ').split()
                away_pitcher_display = f"{away_pitcher_name[1]} {away_pitcher_name[0]}" if len(away_pitcher_name) >= 2 else away_pitcher_data.get('name', 'Unknown')
                
                home_pitcher_name = home_pitcher_data.get('name', 'Unknown').replace(', ', ' ').split()
                home_pitcher_display = f"{home_pitcher_name[1]} {home_pitcher_name[0]}" if len(home_pitcher_name) >= 2 else home_pitcher_data.get('name', 'Unknown')
                
                # Calculate comprehensive lineup advantages (including K% data)
                key_matchups = game_report['key_matchups']
                away_lineup_stats = self.calculate_lineup_advantage(key_matchups, home_pitcher_data['name'])
                home_lineup_stats = self.calculate_lineup_advantage(key_matchups, away_pitcher_data['name'])
                
                # Find umpire
                umpire = self.find_game_umpire(umpires, matchup)
                
                # Find betting data
                betting_game = self.find_game_betting_data(betting_games, matchup)
                
                # Create comprehensive game data with K% information
                game_data = {
                    'matchup': matchup,
                    'away_team': away_team,
                    'home_team': home_team,
                    'game_time': betting_game.get('time', 'TBD') if betting_game else 'TBD',
                    'betting_info': self.format_betting_info(betting_game),
                    'away_pitcher': {
                        'name': away_pitcher_display,
                        'arsenal': self.format_pitcher_arsenal(away_pitcher_data)
                    },
                    'home_pitcher': {
                        'name': home_pitcher_display,
                        'arsenal': self.format_pitcher_arsenal(home_pitcher_data)
                    },
                    # Away lineup vs home pitcher
                    'away_lineup_advantage': away_lineup_stats['ba_advantage'],
                    'away_lineup_k_advantage': away_lineup_stats['k_advantage'],
                    'away_season_ba': away_lineup_stats['season_ba'],
                    'away_arsenal_ba': away_lineup_stats['arsenal_ba'],
                    'away_season_k_pct': away_lineup_stats['season_k_pct'],
                    'away_arsenal_k_pct': away_lineup_stats['arsenal_k_pct'],
                    'away_key_performers': away_lineup_stats['top_performers'],
                    # Home lineup vs away pitcher
                    'home_lineup_advantage': home_lineup_stats['ba_advantage'],
                    'home_lineup_k_advantage': home_lineup_stats['k_advantage'],
                    'home_season_ba': home_lineup_stats['season_ba'],
                    'home_arsenal_ba': home_lineup_stats['arsenal_ba'],
                    'home_season_k_pct': home_lineup_stats['season_k_pct'],
                    'home_arsenal_k_pct': home_lineup_stats['arsenal_k_pct'],
                    'home_key_performers': home_lineup_stats['top_performers'],
                    # Umpire data
                    'umpire': umpire['umpire'] if umpire else 'TBA',
                    'umpire_k_boost': umpire['k_boost'] if umpire else '1.0x',
                    'umpire_bb_boost': umpire['bb_boost'] if umpire else '1.0x'
                }
                
                # Generate topic using full team names from betting data if available
                if betting_game:
                    betting_away = betting_game.get('away_team', away_team)
                    betting_home = betting_game.get('home_team', home_team)
                    # Extract just the team name (last word) from "TB Rays" → "Rays"
                    away_display = betting_away.split()[-1] if ' ' in betting_away else away_team
                    home_display = betting_home.split()[-1] if ' ' in betting_home else home_team
                    topic = f"{away_display} at {home_display} MLB Betting Preview"
                else:
                    # Fallback to short codes if no betting data
                    topic = f"{away_team} at {home_team} MLB Betting Preview"
                
                # Dynamic keywords based on game situation
                keywords = [
                    f"{away_team.lower()}", f"{home_team.lower()}", 
                    "mlb betting", "baseball preview", "pitcher analysis",
                    f"{away_pitcher_display.lower().replace(' ', '-')}", 
                    f"{home_pitcher_display.lower().replace(' ', '-')}",
                    "lineup matchups", "umpire analysis"
                ]
                
                # Add situational keywords based on significant advantages
                if abs(away_lineup_stats['ba_advantage']) > 0.015 or abs(home_lineup_stats['ba_advantage']) > 0.015:
                    keywords.extend(["pitcher advantage", "matchup edge"])
                
                if abs(away_lineup_stats['k_advantage']) > 3.0 or abs(home_lineup_stats['k_advantage']) > 3.0:
                    keywords.extend(["strikeout props", "contact advantage"])
                
                if umpire and umpire['umpire'] != 'TBA':
                    k_multiplier = float(umpire['k_boost'].replace('x', ''))
                    if k_multiplier > 1.1:
                        keywords.extend(["strikeout props", "pitcher friendly umpire"])
                    elif k_multiplier < 0.9:
                        keywords.extend(["hitter friendly umpire", "contact plays"])
                
                blog_topics.append({
                    'topic': topic,
                    'keywords': keywords,
                    'game_data': game_data
                })
                
            except Exception as e:
                print(f"❌ Error processing game {matchup}: {e}")
                continue
        
        # ✅ IMPROVED: Sort blog topics by game time (earliest to latest)
        print(f"🔄 Sorting {len(blog_topics)} games by time...")
        blog_topics.sort(key=lambda x: self.parse_game_time_for_sorting(x['game_data'].get('game_time', 'TBD')))
        
        # Debug: Print sorted order
        for i, topic in enumerate(blog_topics):
            game_time = topic['game_data'].get('game_time', 'TBD')
            print(f"  {i+1}. {topic['topic']} - {game_time}")
        
        return blog_topics
