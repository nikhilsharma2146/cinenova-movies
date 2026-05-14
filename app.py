import streamlit as st
import pandas as pd
import base64
import time
import hashlib
import altair as alt
import os
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from data_preprocessing import preprocess_data
from recommendation_engine import MovieRecommender

# Global Session for performance (Thread-safe via cache_resource)
@st.cache_resource
def get_http_session():
    return requests.Session()

# Page Configuration
st.set_page_config(
    page_title="CineNova Movies | Discover Your Next Favorite",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for CineNova Theme
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    :root {
        --primary: #E50914; /* Cinematic Red */
        --dark-bg: #000000; /* Pure Black */
        --card-bg: #141414; /* Deep Charcoal */
        --text-light: #ffffff;
        --text-muted: #a3a3a3;
    }
    
    /* Global Styles */
    .stApp {
        background-color: var(--dark-bg);
        color: var(--text-light);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Defaults */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        max-width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* Cinematic Navbar */
    .cinenova-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        margin-bottom: 40px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    @keyframes running-neon {
        0% { background-position: 0% 50%; box-shadow: 0 0 10px rgba(229, 9, 20, 0.4); }
        50% { box-shadow: 0 0 25px rgba(229, 9, 20, 0.8); }
        100% { background-position: 200% 50%; box-shadow: 0 0 10px rgba(229, 9, 20, 0.4); }
    }
    .cinenova-logo-stack {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-right: 40px;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        padding: 10px 20px;
        border-radius: 12px;
        border: 2px solid transparent;
        background: linear-gradient(#000, #000) padding-box,
                    linear-gradient(90deg, #e50914, #ff3b30, #660000, #e50914) border-box;
        background-size: 200% 100%;
        animation: running-neon 4s linear infinite;
    }
    .cinenova-logo-stack:hover {
        transform: scale(1.05) translateY(-2px);
        filter: brightness(1.2);
    }
    .cinenova-logo-img {
        height: 100px;
        width: auto;
        margin-bottom: 5px;
    }
    @keyframes logo-ambiance {
        0% { text-shadow: 0 0 10px rgba(229, 9, 20, 0.6); opacity: 0.9; }
        50% { text-shadow: 0 0 25px rgba(229, 9, 20, 1), 0 0 35px rgba(229, 9, 20, 0.8); opacity: 1; }
        100% { text-shadow: 0 0 10px rgba(229, 9, 20, 0.6); opacity: 0.9; }
    }
    .cinenova-logo-text {
        color: white;
        font-size: 1.1rem;
        font-weight: 900;
        letter-spacing: 6px;
        text-transform: uppercase;
        animation: logo-ambiance 3s infinite ease-in-out;
    }
    .cinenova-links a {
        color: var(--text-light);
        text-decoration: none;
        margin-right: 30px;
        font-size: 1.05rem;
        font-weight: 400;
        transition: color 0.3s ease;
    }
    .cinenova-links a:hover {
        color: var(--text-muted);
    }
    .cinenova-icons {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .icon-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.08);
        color: var(--text-light);
        text-decoration: none;
        transition: all 0.3s ease;
        font-size: 1.2rem;
    }
    .icon-btn:hover {
        background-color: rgba(255, 255, 255, 0.2);
        transform: scale(1.1);
    }
    .avatar-circle {
        width: 40px; 
        height: 40px; 
        background: linear-gradient(135deg, var(--primary), #8b5cf6); 
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 900;
        font-size: 1.2rem;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .avatar-circle:hover {
        transform: scale(1.1);
        box-shadow: 0 0 15px rgba(229, 9, 20, 0.6);
        border: 1px solid white;
    }
    
    /* Metric Cards */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: var(--primary);
        background: rgba(229, 9, 20, 0.05);
    }
    .metric-label {
        color: var(--text-muted);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .metric-value {
        color: var(--text-light);
        font-size: 2rem;
        font-weight: 900;
    }
    .metric-value.highlight {
        color: var(--primary);
    }

    /* Sub-Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .section-title {
        color: var(--text-light);
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Cards - Cinematic Style */
    .row-container {
        display: flex;
        gap: 15px;
        overflow-x: auto;
        padding-bottom: 20px;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
        scroll-behavior: smooth;
        will-change: transform;
    }
    .row-container::-webkit-scrollbar {
        display: none;
    }
    
    .landscape-card {
        min-width: 280px;
        height: 160px;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        background-color: var(--card-bg);
        will-change: transform, box-shadow;
    }
    .landscape-card:hover {
        transform: scale(1.05);
        z-index: 10;
        box-shadow: 0 10px 20px rgba(0,0,0,0.8);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .dynamic-poster {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 20px;
        position: relative;
    }
    
    .poster-title {
        font-size: 1.4rem;
        font-weight: 900;
        color: white;
        text-shadow: 0 4px 10px rgba(0,0,0,0.8);
        line-height: 1.2;
        z-index: 2;
    }
    
    .card-gradient {
        position: absolute;
        bottom: 0; left: 0; right: 0; top: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.2) 50%, transparent 100%);
        z-index: 1;
    }
    
    .card-info {
        position: absolute;
        bottom: 10px;
        left: 15px;
        right: 15px;
        z-index: 3;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .landscape-card:hover .card-info {
        opacity: 1;
    }
    
    .card-meta {
        font-size: 0.8rem;
        color: var(--text-light);
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .match-score {
        color: #46d369; /* Netflix Match Green */
    }
    
    .badge {
        background: var(--primary);
        color: white;
        padding: 2px 6px;
        font-size: 0.6rem;
        font-weight: 900;
        border-radius: 2px;
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 3;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Top 10 Styling */
    .top10-container {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 30px;
        padding-top: 20px;
    }
    .top10-card-wrapper {
        display: flex;
        align-items: flex-end;
        position: relative;
        min-width: 250px;
        height: 250px;
    }
    .top10-number {
        font-size: 220px;
        font-weight: 900;
        line-height: 0.75;
        letter-spacing: -15px;
        color: var(--dark-bg);
        -webkit-text-stroke: 4px #555;
        position: absolute;
        left: -15px;
        bottom: -10px;
        z-index: 1;
    }
    .top10-poster {
        width: 130px;
        height: 195px;
        z-index: 2;
        margin-left: 100px;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
        box-shadow: 0 10px 20px rgba(0,0,0,0.8);
    }
    .top10-card-wrapper:hover .top10-poster {
        transform: scale(1.05) translateY(-5px);
        border: 1px solid rgba(255,255,255,0.3);
    }
    .top10-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .landscape-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    .landscape-card:hover .landscape-img {
        transform: scale(1.05);
    }
    
    /* Search Bar Override */
    div[data-baseweb="input"] input {
        background-color: var(--card-bg) !important;
        background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMi41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxjaXJjbGUgY3g9IjExIiBjeT0iMTEiIHI9IjgiPjwvY2lyY2xlPjxsaW5lIHgxPSIyMSIgeTE9IjIxIiB4Mj0iMTYuNjUiIHkyPSIxNi42NSI+PC9saW5lPjwvc3ZnPg==") !important;
        background-repeat: no-repeat !important;
        background-position: 15px center !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: var(--text-light) !important;
        border-radius: 8px !important;
        padding: 15px 25px 15px 50px !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
        will-change: transform, box-shadow;
    }
    div[data-baseweb="input"] input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 10px rgba(229, 9, 20, 0.3) !important;
    }
    
    /* Search Button Styling */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 60px !important;
        width: 100% !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #ff3b30 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 0 15px rgba(229, 9, 20, 0.4) !important;
    }
    
    /* Tabs styling override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 30px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 0px;
        color: var(--text-muted);
        font-size: 1.2rem;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-light);
        border-bottom: 3px solid var(--primary);
    }
    </style>
    """, unsafe_allow_html=True)

# Data Loading
@st.cache_resource
def load_cinenova_engine():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processed_path = os.path.join(base_dir, 'dataset', 'processed_movies.csv')
    
    if not os.path.exists(processed_path):
        df = preprocess_data()
        df.to_csv(processed_path, index=False)
    else:
        df = pd.read_csv(processed_path)
    return MovieRecommender(df)

@st.cache_data(show_spinner=False)
def get_base64_logo():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, 'assets', 'logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

# Removed redundant imports from here

@st.cache_data(ttl=3600, show_spinner=False)
def get_dashboard_metrics(_df):
    m_movies = len(_df)
    m_genres = _df['genres'].str.split().explode().nunique()
    m_lang = _df['language'].nunique()
    m_score = round(_df['imdb_score'].mean(), 1)
    return m_movies, m_genres, m_lang, m_score

@st.cache_data(ttl=600, show_spinner=False)
def get_curated_home_data(_engine):
    # This caches the random sampling so it's stable and fast
    data = {
        "continue": _engine.df.sample(8, random_state=42),
        "series": _engine.df[_engine.df['genres'].str.contains('Drama|Mystery', na=False)].sort_values('imdb_score', ascending=False).head(10),
        "movies": _engine.get_trending(10),
        "anime": _engine.df[_engine.df['genres'].str.contains('Animation', na=False)].sample(8, random_state=1),
        "teen": _engine.df[_engine.df['genres'].str.contains('Romance|Comedy', na=False)].sample(8, random_state=99),
        "hindi": _engine.df.sample(8, random_state=2),
        "malayalam": _engine.df.sample(8, random_state=3),
        "binge": _engine.df[_engine.df['genres'].str.contains('Action|Adventure', na=False)].sample(8, random_state=4),
        "crime": _engine.df[_engine.df['genres'].str.contains('Crime', na=False)].sort_values('imdb_score', ascending=False).head(8),
        "crime_tv": _engine.df[_engine.df['genres'].str.contains('Crime|Thriller', na=False)].sample(8, random_state=15),
        "new": _engine.df.sort_values('title_year', ascending=False).head(8)
    }
    # Pre-calculate unique movies for prefetching
    all_movies_list = []
    for k, v in data.items():
        if isinstance(v, pd.DataFrame) and not v.empty:
            all_movies_list.extend(list(zip(v['movie_title'], v['title_year'])))
    data['prefetch'] = list(set(all_movies_list))
    return data

@st.cache_data(show_spinner=False)
def fetch_tmdb_poster(title, year=None):
    if not title: return None
    
    clean_title = title.strip().replace('\xa0', '').replace('  ', ' ')
    query = urllib.parse.quote(clean_title)
    
    api_keys = [
        "8265bd1679663a7ea12ac168da84d2e8",
        "15d2ea6d0dc1d476efbca3eba2b9bbfb",
        "c272378f44d56715f606412e680a6c0c"
    ]
    
    session = get_http_session()
    
    def try_fetch(url_str):
        for key in api_keys:
            try:
                final_url = url_str.replace("API_KEY_PLACEHOLDER", key)
                res = session.get(final_url, timeout=2) # Reduced timeout
                if res.status_code == 200:
                    data = res.json()
                    if data.get('results'):
                        result = data['results'][0]
                        path = result.get('backdrop_path') or result.get('poster_path')
                        if path:
                            return f"https://image.tmdb.org/t/p/w342{path}"
                        return None
                    return None # No results found, don't try other keys
                elif res.status_code == 404:
                    return None # Not found, don't try other keys
                # If 429 (Rate Limit) or 5xx, try next key
            except:
                continue
        return None

    # Strategy 1: Search with Year
    if year and year != "N/A" and year != 0:
        url = f"https://api.themoviedb.org/3/search/movie?api_key=API_KEY_PLACEHOLDER&query={query}&primary_release_year={year}"
        result = try_fetch(url)
        if result: return result

    # Strategy 2: Search without Year
    url = f"https://api.themoviedb.org/3/search/movie?api_key=API_KEY_PLACEHOLDER&query={query}"
    return try_fetch(url)

@st.cache_data(show_spinner=False)
def prefetch_posters(movie_data_list):
    # Filter unique movies to avoid redundant calls
    unique_movies = list(set(movie_data_list))
    
    def fetch_helper(data):
        return fetch_tmdb_poster(data[0], data[1])
        
    with ThreadPoolExecutor(max_workers=30) as executor: # Increased workers
        list(executor.map(fetch_helper, unique_movies))

def get_gradient_colors(title):
    # Hash title to generate consistent, cinematic gradient pairs
    seed = int(hashlib.sha256(title.encode('utf-8')).hexdigest(), 16)
    palettes = [
        ("#1a2a6c", "#b21f1f"), # Blue to Red
        ("#0f2027", "#203a43"), # Deep Slate
        ("#4b1248", "#f0c27b"), # Purple to Gold
        ("#141E30", "#243B55"), # Midnight
        ("#e52d27", "#b31217"), # Blood Red
        ("#000000", "#434343"), # Black
        ("#23074d", "#cc5333"), # Dark Purple to Orange
    ]
    return palettes[seed % len(palettes)]

def render_navbar():
    logo_b64 = get_base64_logo()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="cinenova-logo-img">' if logo_b64 else ''
    
    st.markdown(f"""
    <div class="cinenova-nav">
        <div style="display: flex; align-items: center;">
            <a href="?nav=Home" target="_self" style="text-decoration: none;">
                <div class="cinenova-logo-stack">
                    {logo_html}
                    <div class="cinenova-logo-text">CINENOVA</div>
                </div>
            </a>
            <div class="cinenova-links">
                <a href="?nav=Home" target="_self">Home</a>
                <a href="?nav=Binge" target="_self">Shows</a>
                <a href="?nav=TopRated" target="_self">Movies</a>
                <a href="?nav=Collection" target="_self">My List</a>
            </div>
        </div>
        <div class="cinenova-icons">
            <a href="?nav=Notifications" class="icon-btn" title="Notifications">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
            </a>
            <a href="?nav=Profile" class="avatar-circle" title="Profile">C</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_landscape_card(movie, badge=None):
    title = movie['movie_title']
    genre = movie['genres'].split()[0] if movie['genres'] else "Drama"
    color1, color2 = get_gradient_colors(title)
    
    # Handle NaN or float title_year gracefully
    try:
        year = int(float(movie['title_year'])) if pd.notna(movie['title_year']) else "N/A"
    except:
        year = "N/A"
        
    badge_html = f'<div class="badge">{badge}</div>' if badge else ""
    
    poster_url = fetch_tmdb_poster(title, year)
    if poster_url:
        bg_html = f'<img src="{poster_url}" class="landscape-img" alt="{title}" loading="lazy">'
    else:
        bg_html = f'<div class="dynamic-poster" style="background: linear-gradient(135deg, {color1}, {color2});"><div class="poster-title">{title}</div></div>'
    
    html = f"""<div class="landscape-card">
<div style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;">
{bg_html}
<div class="card-gradient"></div>
</div>
<div class="card-info">
<div class="card-meta">
<span class="match-score">98% Match</span> 
<span>{year}</span> 
<span style="border: 1px solid rgba(255,255,255,0.4); padding: 0 4px; border-radius: 2px;">HD</span>
</div>
<div style="font-size: 0.8rem; margin-top: 4px;">{genre} • ★ {movie['imdb_score']}</div>
</div>
{badge_html}
</div>"""
    return html

def render_top10_card(movie, rank):
    title = movie['movie_title']
    try:
        year = int(float(movie['title_year'])) if pd.notna(movie['title_year']) else None
    except:
        year = None
        
    color1, color2 = get_gradient_colors(title)
    
    poster_url = fetch_tmdb_poster(title, year)
    if poster_url:
        bg_html = f'<img src="{poster_url}" class="top10-img" alt="{title}" loading="lazy">'
    else:
        bg_html = f'<div class="dynamic-poster" style="background: linear-gradient(135deg, {color1}, {color2}); padding: 10px;"><div class="poster-title" style="font-size: 1rem;">{title}</div></div>'
        
    html = f"""<div class="top10-card-wrapper">
<div class="top10-number">{rank}</div>
<div class="top10-poster">
{bg_html}
</div>
</div>"""
    return html

def render_horizontal_row(df, badge="Recently added"):
    html = '<div class="row-container">'
    for _, row in df.iterrows():
        html += render_landscape_card(row, badge)
    html += '</div>'
    return html

def render_top10_row(df):
    html = '<div class="top10-container">'
    for i, (_, row) in enumerate(df.iterrows()):
        html += render_top10_card(row, i+1)
    html += '</div>'
    return html

def render_grid(df, badge=""):
    for i in range(0, len(df), 5):
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(df):
                with cols[j]:
                    st.markdown(render_landscape_card(df.iloc[i+j], badge=badge), unsafe_allow_html=True)

def main():
    local_css()
    render_navbar()
    
    engine = load_cinenova_engine()
    
    if engine.df.empty:
        st.error("🌌 The CineNova universe is currently empty. Please check your dataset files.")
        return
    
    nav = st.query_params.get("nav", "Home")
    
    if nav == "Binge":
        st.markdown("<div class='section-title'>Binge-Worthy Shows</div>", unsafe_allow_html=True)
        shows = engine.df[engine.df['genres'].str.contains('Action|Adventure|Sci-Fi', na=False)].sample(20, random_state=42)
        prefetch_posters(list(zip(shows['movie_title'], shows['title_year'])))
        render_grid(shows, badge="Trending")
        
    elif nav == "TopRated":
        st.markdown("<div class='section-title'>Top Rated Masterpieces</div>", unsafe_allow_html=True)
        top_rated = engine.get_top_rated(20)
        prefetch_posters(list(zip(top_rated['movie_title'], top_rated['title_year'])))
        render_grid(top_rated, badge="Must Watch")
        
    elif nav == "Collection":
        st.markdown("<div class='section-title'>My Collection</div>", unsafe_allow_html=True)
        st.info("Your collection is currently empty. Start exploring to add some movies!")
        
    elif nav == "Notifications":
        st.markdown("<div class='section-title'>Notifications</div>", unsafe_allow_html=True)
        st.warning("You have no new notifications.")
        st.info("New Arrival: We just added 50+ classic movies to the CineNova vault!")
        
    elif nav == "Profile":
        st.markdown("<div class='section-title'>User Profile</div>", unsafe_allow_html=True)
        st.success("Welcome back, Cinephile!")
        st.markdown("### Account Details")
        st.write("Plan: **Premium Ultra HD**")
        st.write("Member Since: **May 2026**")
        if st.button("Sign Out", type="primary"):
            st.warning("Sign out functionality coming soon.")
        
    else:
        # 1. Metric Overview (Cached)
        m_movies, m_genres, m_lang, m_score = get_dashboard_metrics(engine.df)
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-label">Movies</div>
                <div class="metric-value highlight">{m_movies:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Genres</div>
                <div class="metric-value">{m_genres}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Languages</div>
                <div class="metric-value">{m_lang}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Score</div>
                <div class="metric-value highlight">{m_score} ★</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Functional Discovery Tabs
        sub_nav = st.tabs(["🔍 Discover", "🎭 Mood", "🔗 Similar", "📊 Analytics"])
        
        with sub_nav[0]:
            # Netflix Style Home View
            s_col1, s_col2 = st.columns([0.85, 0.15])
            with s_col1:
                search_query = st.text_input("", placeholder="Search for epic movies, shows, or genres...", label_visibility="collapsed")
            with s_col2:
                search_clicked = st.button("Search")
            
            if search_query:
                st.markdown("<div class='section-title'>Search Results</div>", unsafe_allow_html=True)
                results = engine.search_movies(search_query)
                if not results.empty:
                    st.markdown(render_horizontal_row(results.head(10), "Match"), unsafe_allow_html=True)
                else:
                    st.warning("No matches found in the CineNova universe.")
            else:
                # Get cached data for fast loading
                home_data = get_curated_home_data(engine)
                
                # Prefetch all posters in parallel using pre-calculated list
                prefetch_posters(home_data.get('prefetch', []))

                # 1. Continue Watching for You
                st.markdown("<div class='section-title' style='margin-top: 1rem;'>Continue Watching for You</div>", unsafe_allow_html=True)
                st.markdown(render_horizontal_row(home_data["continue"], "Recently added"), unsafe_allow_html=True)

                # 2. Top 10 Series
                st.markdown("<div class='section-title'>Top 10 Series in CineNova Today</div>", unsafe_allow_html=True)
                st.markdown(render_top10_row(home_data["series"]), unsafe_allow_html=True)

                # 3. Top 10 Movies
                st.markdown("<div class='section-title'>Top 10 Movies in CineNova Today</div>", unsafe_allow_html=True)
                st.markdown(render_top10_row(home_data["movies"]), unsafe_allow_html=True)

        with sub_nav[1]:
            st.markdown("<div class='section-title'>What's your mood today?</div>", unsafe_allow_html=True)
            mood_col1, mood_col2, mood_col3, mood_col4 = st.columns(4)
            selected_mood = None
            if mood_col1.button("🔥 Thrilled", use_container_width=True): selected_mood = "Action"
            if mood_col2.button("❤️ Romantic", use_container_width=True): selected_mood = "Romance"
            if mood_col3.button("🧠 Brainy", use_container_width=True): selected_mood = "Sci-Fi"
            if mood_col4.button("😂 Funny", use_container_width=True): selected_mood = "Comedy"
            
            if selected_mood:
                mood_results = engine.df[engine.df['genres'].str.contains(selected_mood, na=False)].head(10)
                st.markdown(render_horizontal_row(mood_results, "Mood Match"), unsafe_allow_html=True)
            else:
                st.info("Pick a mood to get instant recommendations.")

        with sub_nav[2]:
            st.markdown("<div class='section-title'>Find Something Similar</div>", unsafe_allow_html=True)
            target_movie = st.selectbox("Select a movie you loved:", engine.df['movie_title'].unique())
            if target_movie:
                similar_movies = engine.get_recommendations(target_movie)
                if not similar_movies.empty:
                    st.markdown(render_horizontal_row(similar_movies, "Similar"), unsafe_allow_html=True)

        with sub_nav[3]:
            st.markdown("<div class='section-title'>CineNova Analytics</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.write("### Ratings Distribution")
                chart = alt.Chart(engine.df).mark_bar(color='#e50914').encode(
                    x=alt.X('imdb_score:Q', bin=True, title='IMDb Score'),
                    y=alt.Y('count():Q', title='Number of Movies')
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            with c2:
                st.write("### Top Genres")
                genre_counts = engine.df['genres'].str.split().explode().value_counts().head(10).reset_index()
                genre_counts.columns = ['Genre', 'Count']
                chart2 = alt.Chart(genre_counts).mark_bar(color='#ff3b30').encode(
                    y=alt.Y('Genre:N', sort='-x'),
                    x='Count:Q'
                ).properties(height=300)
                st.altair_chart(chart2, use_container_width=True)

        # Rest of the Home rows (below the tabs)
        if not search_query:
            home_data = get_curated_home_data(engine)

            # 4. Japanese Anime
            st.markdown("<div class='section-title'>Japanese Anime</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["anime"], "New Episode"), unsafe_allow_html=True)
            
            # 5. Teen TV Shows
            st.markdown("<div class='section-title'>Teen TV Shows</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["teen"], "Recently added"), unsafe_allow_html=True)
            
            # 6. Trending in Hindi
            st.markdown("<div class='section-title'>Trending in Hindi</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["hindi"], "Global Hit"), unsafe_allow_html=True)
            
            # 7. Malayalam Cinema
            st.markdown("<div class='section-title'>Malayalam Cinema</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["malayalam"], "Critically Acclaimed"), unsafe_allow_html=True)
            
            # 8. Binge-Worthy Content
            st.markdown("<div class='section-title'>Binge-Worthy Content</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["binge"], "Top Rated"), unsafe_allow_html=True)
            
            # 9. Grit & Crime
            st.markdown("<div class='section-title'>Grit & Crime</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["crime"], "Must Watch"), unsafe_allow_html=True)
            
            # 10. Crime TV Thrillers
            st.markdown("<div class='section-title'>Crime TV Thrillers</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["crime_tv"], "Binge Now"), unsafe_allow_html=True)
            
            # 11. New Releases
            st.markdown("<div class='section-title'>New Releases</div>", unsafe_allow_html=True)
            st.markdown(render_horizontal_row(home_data["new"], "2024 Release"), unsafe_allow_html=True)

            # Footer
            st.markdown(render_footer(), unsafe_allow_html=True)

def render_footer():
    html = """
    <style>
    .footer-container {
        margin-top: 80px;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    .footer-card {
        background-color: #2e2e2e;
        border: 1px solid rgba(184, 162, 70, 0.4);
        border-radius: 6px;
        padding: 35px 20px;
        text-align: center;
        width: 100%;
        max-width: 1000px;
    }
    .footer-text-1 {
        color: #f4d03f;
        font-size: 1.1rem;
        margin-bottom: 15px;
        font-weight: 500;
    }
    .footer-text-2 {
        color: #58d68d;
        font-size: 1.05rem;
        margin-bottom: 30px;
        font-weight: 500;
    }
    .footer-buttons {
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
    }
    .app-btn {
        background: linear-gradient(145deg, #3a3a3a, #1f1f1f);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 10px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
        min-width: 180px;
        position: relative;
        overflow: hidden;
    }
    .app-btn::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg) translateY(-100%);
        transition: transform 0.6s ease;
    }
    .app-btn:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.5), 0 0 15px rgba(255,255,255,0.1);
        border-color: rgba(255,255,255,0.3);
    }
    .app-btn:hover::before {
        transform: rotate(45deg) translateY(100%);
    }
    .app-btn-icon svg {
        fill: white;
        width: 24px;
        height: 24px;
    }
    .app-btn-text {
        text-align: left;
        line-height: 1.2;
    }
    .app-btn-small {
        font-size: 0.7rem;
        opacity: 0.9;
        display: block;
    }
    .app-btn-large {
        font-size: 0.95rem;
        font-weight: 600;
        display: block;
    }
    .footer-copyright {
        margin-top: 25px;
        color: #7f8c8d;
        font-size: 1.3rem;
        font-weight: 400;
    }
    </style>
    
    <div class="footer-container">
        <div class="footer-card">
            <div class="footer-text-1">Experience the ultimate streaming universe with CineNova, bringing you blockbuster movies, exclusive series, and critically-acclaimed originals all in one seamless platform.</div>
            <div class="footer-text-2">Stay Connected with Us and Share with your friends and family.</div>
            <div class="footer-buttons">
                <a href="#" class="app-btn">
                    <div class="app-btn-icon">
                        <svg viewBox="0 0 24 24"><path d="M5 4v16l15-8z"/></svg>
                    </div>
                    <div class="app-btn-text">
                        <span class="app-btn-small">Download APK</span>
                        <span class="app-btn-large">Android App</span>
                    </div>
                </a>
                <a href="#" class="app-btn">
                    <div class="app-btn-icon">
                        <svg viewBox="0 0 384 512"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>
                    </div>
                    <div class="app-btn-text">
                        <span class="app-btn-small">Make on Browser</span>
                        <span class="app-btn-large">IOS APP</span>
                    </div>
                </a>
            </div>
        </div>
        <div class="footer-copyright">© 2026 CineNova.app - Inc.</div>
    </div>
    """
    return html

if __name__ == "__main__":
    main()
