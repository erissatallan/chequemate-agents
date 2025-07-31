"""
Chess Gameplay Visualization Module - Langflow Component

This module provides comprehensive visualization tools for analyzing chess players' 
opening preferences, playing style, and performance characteristics based on their 
chess.com game data.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import cloudscraper
from collections import Counter
import re
import io
import base64

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data, Message
from datetime import datetime


class chess_visualizer(Component):
    display_name = "Chess Style Visualizer"
    description = "Generates comprehensive chess style visualizations including opening analysis and player profiles."
    icon = "chart-line"
    name = "chess_visualizer"

    # Define the input and output schema
    inputs = [
        MessageTextInput(
            name="username",
            display_name="Username",
            info="Enter chess.com username for visualization",
            value="guessworkceoke",
            required=True
        )
    ]

    outputs = [
        Output(
            display_name="HTML Report",
            name="html_report",
            description="HTML report with embedded charts for file saving",
            method="generate_html_report"
        ),
        Output(
            display_name="File Info",
            name="file_info", 
            description="Information about the generated file",
            method="generate_file_info"
        ),
        Output(
            display_name="Text Summary", 
            name="text_summary",
            description="Text-based analysis summary",
            method="generate_text_summary"
        )
    ]

    def generate_html_report(self) -> Message:
        """Generate HTML report with embedded images for file saving."""
        username = self.username
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            visualizer = ChessVisualizerCore()
            
            # Generate comprehensive chart
            comprehensive_chart = visualizer.generate_comprehensive_viz(username)
            
            # Generate spider chart  
            spider_chart = visualizer.generate_spider_chart(username)
            
            if comprehensive_chart and spider_chart:
                # Create complete HTML document
                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Analysis Report - {username}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .chart-section {{
            margin-bottom: 40px;
            padding: 20px;
            border-radius: 8px;
            background: #fafafa;
        }}
        .chart-title {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .chart-image {{
            width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .footer {{
            background: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .timestamp {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Chess Style Analysis Report</h1>
            <h2>{username}</h2>
            <p class="timestamp">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </div>
        
        <div class="content">
            <div class="chart-section">
                <h2 class="chart-title">📊 Comprehensive Opening Analysis</h2>
                <img src="{comprehensive_chart}" class="chart-image" alt="Comprehensive Chess Analysis">
                <p>This comprehensive analysis shows your opening preferences across ECO families, top played openings, family distribution, and key statistics.</p>
            </div>
            
            <div class="chart-section">
                <h2 class="chart-title">🕷️ Player Profile Spider Chart</h2>
                <img src="{spider_chart}" class="chart-image" alt="Chess Profile Spider Chart">
                <p>The spider chart visualizes your playing style across 8 key metrics including tactical play, positional understanding, opening knowledge, and consistency.</p>
            </div>
        </div>
        
        <div class="footer">
            <h3>✅ Analysis Complete!</h3>
            <p>This comprehensive chess analysis was generated from your recent chess.com games.</p>
            <p>Report includes opening preferences, playing style metrics, and detailed performance characteristics.</p>
            <p class="timestamp">File: chess_analysis_{username}_{timestamp}.html</p>
        </div>
    </div>
</body>
</html>"""
                
                return Message(text=html_content)
            else:
                error_html = f"""<!DOCTYPE html>
<html><head><title>Chess Analysis Error</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px;">
        <h3>❌ Visualization Failed</h3>
        <p>Could not generate visualizations for username: <strong>{username}</strong></p>
        <p>Please check:</p>
        <ul>
            <li>Username exists on chess.com</li>
            <li>User has played recent games</li>
            <li>API access is available</li>
        </ul>
    </div>
</body></html>"""
                return Message(text=error_html)
                
        except Exception as e:
            error_html = f"""<!DOCTYPE html>
<html><head><title>Chess Analysis Error</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px;">
        <h3>❌ Error Occurred</h3>
        <p>An error occurred while generating visualizations for <strong>{username}</strong>:</p>
        <p><code>{str(e)}</code></p>
    </div>
</body></html>"""
            return Message(text=error_html)

    def generate_file_info(self) -> Message:
        """Generate file information for the Save File component."""
        username = self.username
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chess_analysis_{username}_{timestamp}"
        
        file_info = f"""File Details:
• Filename: {filename}.html
• Username: {username}
• Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
• Content: Complete HTML report with embedded base64 images
• Format: Self-contained HTML file (no external dependencies)

This file can be opened in any web browser to view the interactive charts and analysis."""
        
        return Message(text=file_info)

    def generate_visualizations(self) -> Data:
        """Generate comprehensive chess visualizations for the given username."""
        username = self.username
        
        try:
            visualizer = ChessVisualizerCore()
            
            # Generate comprehensive chart
            comprehensive_chart = visualizer.generate_comprehensive_viz(username)
            
            # Generate spider chart  
            spider_chart = visualizer.generate_spider_chart(username)
            
            if comprehensive_chart and spider_chart:
                # Create HTML output with embedded images
                html_output = f"""
<div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
    <h1 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
        🎯 Chess Style Analysis: {username}
    </h1>
    
    <div style="margin-bottom: 40px;">
        <h2 style="color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
            📊 Comprehensive Opening Analysis
        </h2>
        <img src="{comprehensive_chart}" style="width: 100%; max-width: 1000px; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" alt="Comprehensive Chess Analysis">
    </div>
    
    <div style="margin-bottom: 40px;">
        <h2 style="color: #34495e; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
            🕷️ Player Profile Spider Chart
        </h2>
        <img src="{spider_chart}" style="width: 100%; max-width: 800px; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" alt="Chess Profile Spider Chart">
    </div>
    
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-top: 30px;">
        <h3 style="margin-top: 0;">✅ Analysis Complete!</h3>
        <p>Generated comprehensive chess style visualizations for <strong>{username}</strong>.</p>
        <p>The analysis includes opening preferences, playing style metrics, and detailed performance characteristics.</p>
    </div>
</div>
                """
                
                return Data(value=html_output)
            else:
                error_html = f"""
<div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <h3 style="margin-top: 0;">❌ Visualization Failed</h3>
    <p>Could not generate visualizations for username: <strong>{username}</strong></p>
    <p>Please check:</p>
    <ul>
        <li>Username exists on chess.com</li>
        <li>User has played recent games</li>
        <li>API access is available</li>
    </ul>
</div>
                """
                return Data(value=error_html)
                
        except Exception as e:
            error_html = f"""
<div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <h3 style="margin-top: 0;">❌ Error Occurred</h3>
    <p>An error occurred while generating visualizations for <strong>{username}</strong>:</p>
    <p><code>{str(e)}</code></p>
</div>
            """
            return Data(value=error_html)

    def generate_text_summary(self) -> Data:
        """Generate a text-based summary as fallback."""
        username = self.username
        
        try:
            visualizer = ChessVisualizerCore()
            games = visualizer.get_user_matches(username, months=3)
            
            if not games:
                return Data(value=f"❌ No games found for {username}")
            
            # Extract analysis data
            codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                     for g in games if '[ECO' in g["pgn"]]
            
            if not codes:
                return Data(value=f"❌ No ECO data found for {username}")
            
            code_counts = Counter(codes)
            rating = visualizer.get_current_rating(username, games)
            streak = visualizer.get_streak(username, games)
            
            # Generate text summary
            total_games = len(games)
            games_with_eco = len(codes)
            unique_openings = len(code_counts)
            most_played = code_counts.most_common(1)[0] if code_counts else ("N/A", 0)
            
            # Family distribution
            family_counts = Counter(code[0] for code in codes)
            family_names = {'A': 'Flank', 'B': 'Semi-Open', 'C': 'Open', 'D': 'Closed', 'E': 'Indian'}
            
            summary = f"""
🎯 CHESS ANALYSIS SUMMARY: {username}
{'='*50}

📊 BASIC STATISTICS:
• Total Games Analyzed: {total_games}
• Games with ECO Data: {games_with_eco} ({(games_with_eco/total_games*100):.1f}%)
• Current Rating: {rating}
• Recent Streak: {streak:+d}
• Unique Openings: {unique_openings}
• Favorite Opening: {most_played[0]} ({most_played[1]} games)

🏰 OPENING FAMILIES:
"""
            for family, count in family_counts.most_common():
                percentage = (count / len(codes)) * 100
                name = family_names.get(family, family)
                summary += f"• {name} ({family}): {count} games ({percentage:.1f}%)\n"
            
            summary += f"""
🎮 TOP 10 OPENINGS:
"""
            for i, (opening, count) in enumerate(code_counts.most_common(10), 1):
                percentage = (count / len(codes)) * 100
                summary += f"{i:2d}. {opening}: {count} games ({percentage:.1f}%)\n"
            
            # Calculate simple metrics
            tactical_score = min((sum(1 for c in codes if c[0] in 'BC') / len(codes)) * 100, 100)
            positional_score = min((sum(1 for c in codes if c[0] in 'DE') / len(codes)) * 100, 100)
            diversity_score = (unique_openings / len(codes)) * 100
            
            summary += f"""
🎯 STYLE METRICS:
• Tactical Preference: {tactical_score:.1f}% (Openings B&C)
• Positional Preference: {positional_score:.1f}% (Openings D&E) 
• Opening Diversity: {diversity_score:.1f}%
• Rating Level: {min((rating/2200)*100, 100):.1f}%

📈 RECOMMENDATIONS:
"""
            if tactical_score < 30:
                summary += "• Consider studying more tactical openings (B00-B99, C00-C99)\n"
            if positional_score < 30:
                summary += "• Try more positional openings (D00-D99, E00-E99)\n"
            if diversity_score < 10:
                summary += "• Expand your opening repertoire for better versatility\n"
            if unique_openings < 5:
                summary += "• Learn more opening variations to improve adaptability\n"
            
            summary += f"\n✅ Analysis complete! Check Langflow's HTML output for visual charts."
            
            return Data(value=summary)
            
        except Exception as e:
            return Data(value=f"❌ Error generating summary for {username}: {str(e)}")


class ChessVisualizerCore:
    """
    A comprehensive chess visualization toolkit for analyzing player styles and preferences.
    """
    
    def __init__(self):
        """Initialize the visualizer with ECO codes and scraper."""
        self.ECO_CODES = [f"{c}{i:02d}" for c in "ABCDE" for i in range(100)]
        self.scraper = cloudscraper.create_scraper(browser={"custom": "ChessVisualizer/1.0"})
    
    def get_user_matches(self, username, months=3):
        """
        Fetch up to `months` worth of monthly archives from chess.com.
        
        Args:
            username (str): Chess.com username
            months (int): Number of recent months to fetch
            
        Returns:
            list: List of game dictionaries
        """
        try:
            # Get all archive URLs
            archives = self.scraper.get(
                f"https://api.chess.com/pub/player/{username}/games/archives"
            ).json()["archives"]
            
            # Take only the last `months` URLs
            recent_urls = archives[-months:]
            games = []
            
            # Fetch each archive and extend the games list
            for url in recent_urls:
                month_games = self.scraper.get(url).json().get("games", [])
                games.extend(month_games)
                
            print(f"✅ Successfully fetched {len(games)} games for {username}")
            return games
            
        except Exception as e:
            print(f"❌ Error fetching games for {username}: {e}")
            return []
    
    def get_current_rating(self, username, games):
        """Extract the latest rating for username from their most recent game."""
        if not games:
            return 1200  # Default rating
        
        last = games[0]
        player = last["white"] if last["white"]["username"].lower() == username.lower() else last["black"]
        return player["rating"]
    
    def get_streak(self, username, games, max_checks=10):
        """Compute win(+) or loss(-) streak over the last up to max_checks games."""
        streak = 0
        for game in games[:max_checks]:
            player = game["white"] if game["white"]["username"].lower() == username.lower() else game["black"]
            result = player["result"]
            
            if result == "win":
                streak = streak + 1 if streak >= 0 else 1
            elif result in ("checkmated", "timeout", "resigned"):
                streak = streak - 1 if streak <= 0 else -1
            else:
                break  # Draw or other result breaks streak
        return streak
    
    def get_time_preferences(self, games):
        """Return a dict mapping time_control → fraction of games played."""
        counts = Counter(g["time_control"] for g in games)
        total = sum(counts.values()) or 1
        return {tc: round(cnt/total, 2) for tc, cnt in counts.items()}
    
    def get_style_vector(self, games):
        """Build a normalized vector representing frequencies of openings played."""
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        counts = Counter(codes)
        vec = np.array([counts.get(code, 0) for code in self.ECO_CODES], dtype=float)
        return vec / (vec.sum() or 1)
    
    def comprehensive_style_visualization(self, username, top_n=15):
        """
        Create a comprehensive 4-panel visualization of opening style.
        
        Args:
            username (str): Chess.com username
            top_n (int): Number of top openings to display
        """
        games = self.get_user_matches(username, months=3)
        if not games:
            print(f"No games found for {username}")
            return None, None
        
        # Get the style vector and extract ECO codes
        style_vec = self.get_style_vector(games)
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        code_counts = Counter(codes)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Chess Opening Style Analysis for {username}", fontsize=16, fontweight='bold')
        
        # 1. Heatmap of ECO codes
        heatmap_data = style_vec.reshape(5, 100)
        opening_families = ['A (Flank)', 'B (Semi-Open)', 'C (Open)', 'D (Closed)', 'E (Indian)']
        
        sns.heatmap(heatmap_data, ax=ax1, cmap='YlOrRd', 
                    yticklabels=opening_families, xticklabels=False,
                    cbar_kws={'label': 'Frequency'})
        ax1.set_title('Opening Frequency Heatmap by ECO Families', fontweight='bold')
        ax1.set_xlabel('ECO Codes (00-99)')
        
        # 2. Bar chart of top openings
        if code_counts:
            top_openings = code_counts.most_common(top_n)
            codes_list, counts_list = zip(*top_openings)
            
            bars = ax2.bar(range(len(codes_list)), counts_list, color='steelblue', alpha=0.7)
            ax2.set_xlabel('ECO Codes')
            ax2.set_ylabel('Games Played')
            ax2.set_title(f'Top {len(codes_list)} Most Played Openings', fontweight='bold')
            ax2.set_xticks(range(len(codes_list)))
            ax2.set_xticklabels(codes_list, rotation=45)
            
            # Add value labels
            for bar, count in zip(bars, counts_list):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha='center', va='bottom', fontsize=9)
        else:
            ax2.text(0.5, 0.5, 'No ECO data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Top Openings (No Data)', fontweight='bold')
        
        # 3. Opening family distribution
        family_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        for code in codes:
            family_counts[code[0]] += 1
        
        if sum(family_counts.values()) > 0:
            families = list(family_counts.keys())
            counts = list(family_counts.values())
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
            
            wedges, texts, autotexts = ax3.pie(counts, labels=families, autopct='%1.1f%%', 
                                              colors=colors, startangle=90)
            ax3.set_title('Distribution by Opening Families', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'No ECO data available', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Opening Family Distribution (No Data)', fontweight='bold')
        
        # 4. Summary statistics
        ax4.axis('off')
        total_games = len(games)
        games_with_eco = len(codes)
        unique_openings = len(code_counts)
        most_played = code_counts.most_common(1)[0] if code_counts else ("N/A", 0)
        
        stats_text = f"""
    📊 Style Vector Summary
    
    Total Games Analyzed: {total_games}
    Games with ECO Codes: {games_with_eco}
    Coverage: {(games_with_eco/total_games*100):.1f}%
    
    Unique Openings Played: {unique_openings}
    Most Played Opening: {most_played[0]} ({most_played[1]} games)
    
    Opening Diversity Score: {len(code_counts)/len(self.ECO_CODES)*100:.2f}%
    (Percentage of all possible openings played)
        """
        
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=11,
                 verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string for Langflow display."""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    
    def generate_comprehensive_viz(self, username):
        """Generate comprehensive visualization and return as base64."""
        games = self.get_user_matches(username, months=3)
        if not games:
            return None
        
        style_vec = self.get_style_vector(games)
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        code_counts = Counter(codes)
        
        # Create comprehensive visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Chess Opening Analysis: {username}", fontsize=16, fontweight='bold')
        
        # 1. Heatmap
        heatmap_data = style_vec.reshape(5, 100)
        opening_families = ['A (Flank)', 'B (Semi-Open)', 'C (Open)', 'D (Closed)', 'E (Indian)']
        
        sns.heatmap(heatmap_data, ax=ax1, cmap='YlOrRd', 
                    yticklabels=opening_families, xticklabels=False,
                    cbar_kws={'label': 'Frequency'})
        ax1.set_title('Opening Frequency Heatmap', fontweight='bold')
        
        # 2. Top openings bar chart
        if code_counts:
            top_openings = code_counts.most_common(10)
            codes_list, counts_list = zip(*top_openings)
            
            bars = ax2.bar(range(len(codes_list)), counts_list, color='steelblue', alpha=0.7)
            ax2.set_xlabel('ECO Codes')
            ax2.set_ylabel('Games Played')
            ax2.set_title('Top 10 Most Played Openings', fontweight='bold')
            ax2.set_xticks(range(len(codes_list)))
            ax2.set_xticklabels(codes_list, rotation=45)
            
            for bar, count in zip(bars, counts_list):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha='center', va='bottom', fontsize=9)
        
        # 3. Family distribution pie chart
        family_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        for code in codes:
            family_counts[code[0]] += 1
        
        if sum(family_counts.values()) > 0:
            families = list(family_counts.keys())
            counts = list(family_counts.values())
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
            
            ax3.pie(counts, labels=families, autopct='%1.1f%%', 
                   colors=colors, startangle=90)
            ax3.set_title('Opening Family Distribution', fontweight='bold')
        
        # 4. Stats summary
        ax4.axis('off')
        total_games = len(games)
        games_with_eco = len(codes)
        unique_openings = len(code_counts)
        most_played = code_counts.most_common(1)[0] if code_counts else ("N/A", 0)
        
        stats_text = f"""📊 Player Statistics

Total Games: {total_games}
ECO Coverage: {(games_with_eco/total_games*100):.1f}%
Unique Openings: {unique_openings}
Favorite Opening: {most_played[0]} ({most_played[1]}x)
Diversity Score: {len(code_counts)/len(self.ECO_CODES)*100:.2f}%"""
        
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=12,
                 verticalalignment='top', 
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def generate_spider_chart(self, username):
        """Generate spider chart and return as base64."""
        games = self.get_user_matches(username, months=3)
        if not games:
            return None
            
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        
        if not codes:
            return None
        
        code_counts = Counter(codes)
        rating = self.get_current_rating(username, games)
        streak = self.get_streak(username, games)
        time_prefs = self.get_time_preferences(games)
        
        # Calculate spider metrics
        metrics = {
            'Tactical Play': min((code_counts.get('B01', 0) + code_counts.get('C02', 0)) / len(codes) * 300, 100),
            'Positional Play': min((code_counts.get('D00', 0) + code_counts.get('A00', 0)) / len(codes) * 300, 100),
            'Opening Knowledge': min((len(set(codes)) / 25) * 100, 100),
            'Aggressive Style': min((sum(1 for c in codes if c[0] in 'BC') / len(codes)) * 100, 100),
            'Solid Defense': min((sum(1 for c in codes if c[0] in 'DE') / len(codes)) * 100, 100),
            'Time Management': min(time_prefs.get('600', 0) * 100 + time_prefs.get('900', 0) * 100, 100),
            'Consistency': min(100 - abs(streak) * 10, 100),
            'Rating Level': min((rating / 2200) * 100, 100),
        }
        
        # Create spider chart
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        fig.suptitle(f"Chess Profile Spider Chart: {username}", fontsize=16, fontweight='bold')
        
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]
        
        ax.plot(angles, values, 'o-', linewidth=3, label=username, color='crimson', markersize=8)
        ax.fill(angles, values, alpha=0.3, color='crimson')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True)
        
        # Add value labels
        for angle, value in zip(angles[:-1], values[:-1]):
            ax.text(angle, value + 5, f'{value:.0f}', ha='center', va='center', 
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def simple_style_visualization(self, username):
        """Create a simple, clean 2-panel visualization of opening preferences."""
        games = self.get_user_matches(username, months=3)
        if not games:
            print(f"No games found for {username}")
            return
        
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        
        if not codes:
            print(f"No ECO data found for {username}")
            return
        
        code_counts = Counter(codes)
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"Opening Style Profile: {username}", fontsize=14, fontweight='bold')
        
        # Opening families distribution
        family_counts = Counter(code[0] for code in codes)
        family_names = {
            'A': 'Flank Openings', 'B': 'Semi-Open Games', 'C': 'Open Games',
            'D': 'Closed Games', 'E': 'Indian Defenses'
        }
        
        families = [family_names.get(f, f) for f in family_counts.keys()]
        counts = list(family_counts.values())
        colors = plt.cm.Set3(range(len(families)))
        
        wedges, texts, autotexts = ax1.pie(counts, labels=families, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax1.set_title('Opening Family Preferences')
        
        # Top 10 specific openings
        top_openings = code_counts.most_common(10)
        if top_openings:
            eco_codes, play_counts = zip(*top_openings)
            
            bars = ax2.barh(range(len(eco_codes)), play_counts, color='skyblue', alpha=0.8)
            ax2.set_yticks(range(len(eco_codes)))
            ax2.set_yticklabels(eco_codes)
            ax2.set_xlabel('Number of Games')
            ax2.set_title('Top 10 Favorite Openings')
            ax2.invert_yaxis()
            
            # Add value labels
            for i, (bar, count) in enumerate(zip(bars, play_counts)):
                ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                        str(count), va='center', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        # Print stats
        total_games = len(codes)
        unique_openings = len(code_counts)
        most_played = code_counts.most_common(1)[0]
        
        print(f"\n📈 Quick Stats for {username}:")
        print(f"   • Games with opening data: {total_games}")
        print(f"   • Different openings played: {unique_openings}")
        print(f"   • Favorite opening: {most_played[0]} ({most_played[1]} times)")
        print(f"   • Opening diversity: {unique_openings/total_games:.2%} (unique openings per game)")
    
    def radar_style_visualization(self, username):
        """Create a radar chart showing opening family preferences and player characteristics."""
        games = self.get_user_matches(username, months=3)
        if not games:
            print(f"No games found for {username}")
            return
        
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        
        if not codes:
            print(f"No ECO data found for {username}")
            return
        
        # Calculate opening family percentages
        family_counts = Counter(code[0] for code in codes)
        total_openings = sum(family_counts.values())
        
        family_names = ['A (Flank)', 'B (Semi-Open)', 'C (Open)', 'D (Closed)', 'E (Indian)']
        family_percentages = []
        
        for family_letter in 'ABCDE':
            count = family_counts.get(family_letter, 0)
            percentage = (count / total_openings) * 100 if total_openings > 0 else 0
            family_percentages.append(percentage)
        
        # Create radar chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), subplot_kw=dict(projection='polar'))
        fig.suptitle(f"Radar Chart Analysis: {username}", fontsize=16, fontweight='bold')
        
        # First radar: Opening families
        angles = np.linspace(0, 2 * np.pi, len(family_names), endpoint=False).tolist()
        family_percentages += family_percentages[:1]
        angles += angles[:1]
        
        ax1.plot(angles, family_percentages, 'o-', linewidth=2, label=username, color='steelblue')
        ax1.fill(angles, family_percentages, alpha=0.25, color='steelblue')
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels(family_names)
        ax1.set_ylim(0, max(family_percentages[:-1]) * 1.2 if family_percentages[:-1] else 10)
        ax1.set_title('Opening Family Distribution (%)', pad=20, fontweight='bold')
        ax1.grid(True)
        
        # Add percentage labels
        for angle, percentage in zip(angles[:-1], family_percentages[:-1]):
            ax1.text(angle, percentage + max(family_percentages[:-1]) * 0.05, 
                    f'{percentage:.1f}%', ha='center', va='center', fontsize=10)
        
        # Second radar: Player characteristics
        rating = self.get_current_rating(username, games)
        streak = self.get_streak(username, games)
        time_prefs = self.get_time_preferences(games)
        
        characteristics = {
            'Rating Level': min((rating / 2000) * 100, 100),
            'Recent Form': min(max((streak + 5) * 10, 0), 100),
            'Blitz Preference': time_prefs.get('60', 0) * 100,
            'Rapid Preference': time_prefs.get('600', 0) * 100,
            'Opening Diversity': min((len(set(codes)) / 20) * 100, 100),
        }
        
        char_names = list(characteristics.keys())
        char_values = list(characteristics.values())
        
        angles2 = np.linspace(0, 2 * np.pi, len(char_names), endpoint=False).tolist()
        char_values += char_values[:1]
        angles2 += angles2[:1]
        
        ax2.plot(angles2, char_values, 'o-', linewidth=2, label=username, color='orange')
        ax2.fill(angles2, char_values, alpha=0.25, color='orange')
        ax2.set_xticks(angles2[:-1])
        ax2.set_xticklabels(char_names)
        ax2.set_ylim(0, 100)
        ax2.set_title('Player Characteristics (0-100%)', pad=20, fontweight='bold')
        ax2.grid(True)
        
        # Add value labels
        for angle, value in zip(angles2[:-1], char_values[:-1]):
            ax2.text(angle, value + 5, f'{value:.0f}', ha='center', va='center', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        # Print summary
        print(f"\n🎯 Radar Chart Summary for {username}:")
        print(f"   • Most played opening family: {family_names[np.argmax(family_percentages[:-1])]}")
        print(f"   • Opening diversity: {characteristics['Opening Diversity']:.1f}/100")
        print(f"   • Rating level: {characteristics['Rating Level']:.1f}/100 (ELO: {rating})")
        print(f"   • Recent form: {characteristics['Recent Form']:.1f}/100 (Streak: {streak})")
    
    def spider_style_visualization(self, username):
        """Create a spider chart showing detailed opening preferences and playing patterns."""
        games = self.get_user_matches(username, months=3)
        if not games:
            print(f"No games found for {username}")
            return
        
        codes = [re.search(r'\[ECO "([A-E]\d{2})"\]', g["pgn"]).group(1) 
                 for g in games if '[ECO' in g["pgn"]]
        
        if not codes:
            print(f"No ECO data found for {username}")
            return
        
        code_counts = Counter(codes)
        
        # Calculate comprehensive metrics
        rating = self.get_current_rating(username, games)
        streak = self.get_streak(username, games)
        time_prefs = self.get_time_preferences(games)
        
        metrics = {
            'Tactical Sharpness': min((code_counts.get('B01', 0) + code_counts.get('C02', 0) + 
                                      code_counts.get('C44', 0)) / len(codes) * 500, 100),
            'Positional Play': min((code_counts.get('D00', 0) + code_counts.get('D06', 0) + 
                                   code_counts.get('A00', 0)) / len(codes) * 500, 100),
            'Opening Knowledge': min((len(set(codes)) / 30) * 100, 100),
            'Aggressive Style': min((sum(1 for c in codes if c[0] in 'BC') / len(codes)) * 100, 100),
            'Solid Defense': min((sum(1 for c in codes if c[0] in 'DE') / len(codes)) * 100, 100),
            'Time Management': min(time_prefs.get('600', 0) * 100 + time_prefs.get('900', 0) * 100, 100),
            'Consistency': min(100 - abs(streak) * 10, 100),
            'Rating Strength': min((rating / 2500) * 100, 100),
        }
        
        # Create spider chart
        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
        fig.suptitle(f"Spider Chart: Detailed Chess Profile - {username}", fontsize=16, fontweight='bold')
        
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]
        
        ax.plot(angles, values, 'o-', linewidth=3, label=username, color='crimson', markersize=8)
        ax.fill(angles, values, alpha=0.3, color='crimson')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True)
        
        # Add value labels
        for angle, value, category in zip(angles[:-1], values[:-1], categories):
            ax.text(angle, value + 5, f'{value:.0f}', ha='center', va='center', 
                    fontsize=10, fontweight='bold', 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        plt.show()
        
        # Analysis
        print(f"\n🕷️ Spider Chart Analysis for {username}:")
        print("=" * 50)
        
        sorted_metrics = sorted(metrics.items(), key=lambda x: x[1], reverse=True)
        strengths = sorted_metrics[:3]
        weaknesses = sorted_metrics[-3:]
        
        print("🔥 Top Strengths:")
        for i, (metric, value) in enumerate(strengths, 1):
            print(f"   {i}. {metric}: {value:.1f}/100")
        
        print("\n📈 Areas for Improvement:")
        for i, (metric, value) in enumerate(weaknesses, 1):
            print(f"   {i}. {metric}: {value:.1f}/100")
        
        overall_score = np.mean(list(metrics.values()))
        if overall_score >= 70:
            style_assessment = "🏆 Elite Player"
        elif overall_score >= 50:
            style_assessment = "⭐ Strong Player"
        elif overall_score >= 30:
            style_assessment = "📚 Developing Player"
        else:
            style_assessment = "🌱 Beginner Player"
        
        print(f"\n🎯 Overall Assessment: {style_assessment} (Score: {overall_score:.1f}/100)")
        
        print(f"\n💡 Style Recommendations:")
        if metrics['Tactical Sharpness'] < 50:
            print("   • Practice tactical puzzles to improve calculation")
        if metrics['Opening Knowledge'] < 50:
            print("   • Study more opening variations to expand repertoire")
        if metrics['Time Management'] < 50:
            print("   • Work on time management in longer time controls")
        if metrics['Consistency'] < 50:
            print("   • Focus on maintaining steady performance")
    
    def generate_all_charts(self, username):
        """
        Generate all available visualizations for a given username.
        
        Args:
            username (str): Chess.com username to analyze
        """
        print(f"🎯 Generating comprehensive chess analysis for: {username}")
        print("=" * 60)
        
        try:
            print("\n📊 1. Comprehensive Style Analysis...")
            self.comprehensive_style_visualization(username)
            
            print("\n📈 2. Simple Style Profile...")
            self.simple_style_visualization(username)
            
            print("\n🎯 3. Radar Chart Analysis...")
            self.radar_style_visualization(username)
            
            print("\n🕷️ 4. Spider Chart Profile...")
            self.spider_style_visualization(username)
            
            print(f"\n✅ Analysis complete for {username}!")
            
        except Exception as e:
            print(f"❌ Error generating charts for {username}: {e}")


# End of ChessVisualizerCore class - no main() function needed for Langflow components
