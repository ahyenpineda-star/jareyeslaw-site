#!/usr/bin/env python3
"""
Auto-update script for Atty. Jen Reyes Media Appearances page.
Searches YouTube, TikTok, and web for new content and updates appearances.html.
"""

import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# Configuration
APPEARANCES_FILE = Path(__file__).parent.parent / "appearances.html"
DATA_FILE = Path(__file__).parent / "known_items.json"

# Known video IDs to avoid duplicates
KNOWN_VIDEOS_KEY = "known_videos"
KNOWN_ARTICLES_KEY = "known_articles"

# Keywords that indicate an Atty. Jen Reyes video
REYES_KEYWORDS = [
    "atty jen", "atty. jen", "attorney jen", "jennifer reyes", 
    "jennifer arlene", "atty jennifer", "atty. jennifer",
    "jen reyes", "j. reyes", "reyes law", "constitutional law"
]

def load_known_items():
    """Load known items from JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {KNOWN_VIDEOS_KEY: [], KNOWN_ARTICLES_KEY: []}

def save_known_items(items):
    """Save known items to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(items, f, indent=2)

def is_reyes_video(title, description=""):
    """Check if a video is likely about Atty. Jen Reyes based on title/description."""
    text = (title + " " + description).lower()
    return any(keyword in text for keyword in REYES_KEYWORDS)

def search_youtube(query, max_results=10):
    """Search YouTube for videos using web scraping."""
    videos = []
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        if response.status_code == 200:
            text = response.text
            
            # Find video data in JSON
            # YouTube stores data in a specific format
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            title_pattern = r'"title":\{"runs":\[\{"text":"([^"]+)"\}'
            
            video_ids = list(set(re.findall(video_pattern, text)))[:max_results*2]
            
            # Try to extract titles
            titles = re.findall(title_pattern, text)
            
            for i, video_id in enumerate(video_ids):
                # Try to find matching title
                title = titles[i] if i < len(titles) else ""
                
                videos.append({
                    'id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'embed_url': f"https://www.youtube.com/embed/{video_id}",
                    'title': title,
                    'source': 'youtube'
                })
    except Exception as e:
        print(f"Error searching YouTube: {e}")
    
    return videos

def search_tiktok_user_videos(username="attyjenreyes", max_results=10):
    """Search TikTok user's videos."""
    videos = []
    user_url = f"https://www.tiktok.com/@{username}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(user_url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Extract video IDs from TikTok page
            video_pattern = r'/video/(\d+)'
            video_ids = list(set(re.findall(video_pattern, response.text)))[:max_results]
            
            for video_id in video_ids:
                videos.append({
                    'id': video_id,
                    'url': f"https://www.tiktok.com/@{username}/video/{video_id}",
                    'embed_url': f"https://www.tiktok.com/embed/v2/{video_id}?autoplay=0",
                    'source': 'tiktok'
                })
    except Exception as e:
        print(f"Error searching TikTok: {e}")
    
    return videos

def search_web_articles(query, max_results=5):
    """Search web for articles about Atty. Jen Reyes."""
    articles = []
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for g in soup.find_all('div', class_='g')[:max_results]:
                link = g.find('a')
                if link and link.get('href'):
                    url = link['href']
                    title_elem = g.find('h3')
                    title = title_elem.text if title_elem else "Article"
                    
                    # Filter for relevant news sites
                    relevant_domains = [
                        'pna.gov.ph', 'abs-cbn.com', 'gmanews.tv', 'inquirer.net',
                        'rappler.com', 'philstar.com', 'manilatimes.net',
                        'bomboradyo.com', 'abogado.com.ph', 'tv5.com.ph',
                        'bilyonaryo.com', 'oneph.one'
                    ]
                    
                    if any(domain in url for domain in relevant_domains):
                        desc_elem = g.find('div', class_='VwiC3b')
                        description = desc_elem.text if desc_elem else ""
                        
                        # Check if article mentions Reyes
                        if is_reyes_video(title, description):
                            articles.append({
                                'url': url,
                                'title': title,
                                'description': description[:200],
                                'source': 'web',
                                'source_name': next((d.split('.')[0] for d in relevant_domains if d in url), 'News')
                            })
    except Exception as e:
        print(f"Error searching web: {e}")
    
    return articles

def generate_video_id(video_info):
    """Generate a unique ID for a video."""
    if video_info['source'] == 'youtube':
        return f"yt_{video_info['id']}"
    elif video_info['source'] == 'tiktok':
        return f"tt_{video_info['id']}"
    return hashlib.md5(video_info['url'].encode()).hexdigest()

def generate_article_id(article_info):
    """Generate a unique ID for an article."""
    return hashlib.md5(article_info['url'].encode()).hexdigest()

def create_video_card(video_info, title=None, description=None, date=None):
    """Create HTML for a video card."""
    if not title:
        title = video_info.get('title', 'New Interview')
    if not description:
        description = f"Recent appearance by Atty. Jen Reyes on {video_info['source'].title()}."
    if not date:
        date = datetime.now().strftime("%B %d, %Y")
    
    if video_info['source'] == 'youtube':
        return f'''
        <div class="video-card">
          <div class="youtube-embed">
            <iframe src="{video_info['embed_url']}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
          </div>
          <div class="video-info">
            <h4>{title}</h4>
            <p>{description}</p>
            <span class="video-date">{date}</span>
          </div>
        </div>'''
    elif video_info['source'] == 'tiktok':
        return f'''
        <div class="video-card">
          <iframe src="{video_info['embed_url']}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>
          <div class="video-info">
            <h4>{title}</h4>
            <p>{description}</p>
            <span class="video-date">{date}</span>
          </div>
        </div>'''
    return ""

def create_article_card(article_info):
    """Create HTML for an article card."""
    return f'''
          <a href="{article_info['url']}" target="_blank" style="display: block; padding: 1rem; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.15); border-radius: 12px; text-decoration: none; transition: all 0.3s;" onmouseover="this.style.borderColor='rgba(168, 85, 247, 0.4)'" onmouseout="this.style.borderColor='rgba(168, 85, 247, 0.15)'">
            <h4 style="color: #a855f7; margin: 0 0 0.5rem 0; font-size: 0.9rem;">{article_info.get('source_name', 'News')}</h4>
            <p style="color: #c4b5d4; margin: 0; font-size: 0.85rem;">{article_info.get('title', 'New article featuring Atty. Jen Reyes.')}</p>
          </a>'''

def find_last_youtube_card_end(content):
    """Find the position after the last YouTube video card."""
    last_yt_pos = -1
    idx = 0
    while True:
        pos = content.find('youtube.com/embed/', idx)
        if pos == -1:
            break
        # Find the end of this video card (next </div> after video-info closing)
        card_end = content.find('</div>\n', pos)
        if card_end != -1:
            last_yt_pos = card_end + len('</div>\n')
        idx = pos + 1
    return last_yt_pos

def find_last_tiktok_card_end(content):
    """Find the position after the last TikTok video card."""
    last_tt_pos = -1
    idx = 0
    while True:
        pos = content.find('tiktok.com/embed/', idx)
        if pos == -1:
            break
        # Find the end of this video card (next </div>\n after video-info closing)
        # TikTok cards end with </div>\n\n or </div>\n
        search_from = pos
        while search_from < len(content):
            next_div = content.find('</div>', search_from)
            if next_div == -1:
                break
            # Check if this looks like the card end (followed by newline and another div or whitespace)
            after = content[next_div:next_div+20]
            if '</div>\n' in after:
                last_tt_pos = next_div + len('</div>\n')
                break
            search_from = next_div + 1
        idx = pos + 1
    return last_tt_pos

def update_appearances_html(new_videos, new_articles):
    """Update the appearances.html file with new content, keeping YouTube before TikTok."""
    with open(APPEARANCES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Separate new videos by source
    new_youtube = [v for v in new_videos if v['source'] == 'youtube']
    new_tiktok = [v for v in new_videos if v['source'] == 'tiktok']
    
    # Generate HTML for new videos
    youtube_html = ""
    for video in new_youtube:
        title = video.get('title', 'New Interview')
        if not title or len(title) < 5:
            title = f"New YouTube Interview"
        youtube_html += create_video_card(video, 
            title=title, 
            description=f"Recent appearance by Atty. Jen Reyes.",
            date=datetime.now().strftime("%B %d, %Y"))
    
    tiktok_html = ""
    for video in new_tiktok:
        title = video.get('title', 'New Interview')
        if not title or len(title) < 5:
            title = f"New TikTok Video"
        tiktok_html += create_video_card(video, 
            title=title, 
            description=f"Recent appearance by Atty. Jen Reyes.",
            date=datetime.now().strftime("%B %d, %Y"))
    
    # Insert YouTube videos after the last YouTube card
    if youtube_html:
        yt_insert_pos = find_last_youtube_card_end(content)
        if yt_insert_pos == -1:
            # Fallback: insert at start of video grid
            yt_insert_pos = content.find('<div class="video-grid">') + len('<div class="video-grid">')
        content = content[:yt_insert_pos] + "\n" + youtube_html + content[yt_insert_pos:]
    
    # After inserting YouTube, recalculate TikTok position
    if tiktok_html:
        tt_insert_pos = find_last_tiktok_card_end(content)
        if tt_insert_pos == -1:
            # No existing TikTok videos — insert before the Follow button
            tt_insert_pos = content.find('Follow Atty. Jen on TikTok')
            if tt_insert_pos != -1:
                # Go back to the start of that line
                tt_insert_pos = content.rfind('<div', 0, tt_insert_pos)
        if tt_insert_pos != -1:
            content = content[:tt_insert_pos] + "\n" + tiktok_html + content[tt_insert_pos:]
    
    # Add new articles
    if new_articles:
        articles_grid_start = content.find('<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.2rem;">')
        if articles_grid_start != -1:
            new_article_html = ""
            for article in new_articles:
                new_article_html += create_article_card(article)
            
            articles_grid_end = content.find('</div>\n      </div>', articles_grid_start)
            if articles_grid_end != -1:
                content = content[:articles_grid_end] + "\n" + new_article_html + content[articles_grid_end:]
    
    # Write updated content
    with open(APPEARANCES_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """Main function to search and update appearances."""
    print(f"Starting update at {datetime.now()}")
    
    # Load known items
    known_items = load_known_items()
    known_videos = set(known_items.get(KNOWN_VIDEOS_KEY, []))
    known_articles = set(known_items.get(KNOWN_ARTICLES_KEY, []))
    
    new_videos = []
    new_articles = []
    
    # Search YouTube for new videos - more specific queries
    youtube_queries = [
        '"Atty Jen Reyes" interview',
        '"Jennifer Arlene Reyes" lawyer',
        '"Atty Jennifer Reyes" constitutional law',
        '"Atty Jen Reyes" Bilyonaryo',
        '"Atty Jen Reyes" Bombo Radyo',
        '"Atty Jen Reyes" One News'
    ]
    
    print("Searching YouTube...")
    for query in youtube_queries:
        videos = search_youtube(query, max_results=5)
        for video in videos:
            video_id = generate_video_id(video)
            if video_id not in known_videos:
                # Only add if title/description mentions Reyes
                if is_reyes_video(video.get('title', ''), ''):
                    new_videos.append(video)
                    known_videos.add(video_id)
                    print(f"  Found new YouTube video: {video['id']} - {video.get('title', '')[:50]}")
    
    # Search TikTok - Atty. Jen's own account
    print("Searching TikTok...")
    videos = search_tiktok_user_videos("attyjenreyes", max_results=10)
    for video in videos:
        video_id = generate_video_id(video)
        if video_id not in known_videos:
            new_videos.append(video)
            known_videos.add(video_id)
            print(f"  Found new TikTok video: {video['id']}")
    
    # Search for articles
    print("Searching for articles...")
    article_queries = [
        '"Atty Jen Reyes" Philippines article',
        '"Jennifer Arlene Reyes" lawyer interview',
        '"Atty Jennifer Reyes" constitutional law professor'
    ]
    
    for query in article_queries:
        articles = search_web_articles(query, max_results=5)
        for article in articles:
            article_id = generate_article_id(article)
            if article_id not in known_articles:
                new_articles.append(article)
                known_articles.add(article_id)
                print(f"  Found new article: {article['title'][:50]}...")
    
    # Update HTML if we found new content
    if new_videos or new_articles:
        print(f"\nFound {len(new_videos)} new videos and {len(new_articles)} new articles")
        if update_appearances_html(new_videos, new_articles):
            print("Successfully updated appearances.html")
        else:
            print("Error updating appearances.html")
    else:
        print("\nNo new content found")
    
    # Save known items
    known_items[KNOWN_VIDEOS_KEY] = list(known_videos)
    known_items[KNOWN_ARTICLES_KEY] = list(known_articles)
    known_items["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    save_known_items(known_items)
    
    print(f"Update completed at {datetime.now()}")

if __name__ == "__main__":
    main()
