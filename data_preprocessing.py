import pandas as pd
import numpy as np
import re
import os

def clean_title(title):
    if not isinstance(title, str):
        return ""
    # Remove weird characters at the end (like the 'A' or non-ascii)
    title = title.strip()
    title = re.sub(r'[^\x00-\x7F]+', '', title)
    return title.strip()

def preprocess_data(file_path=None):
    if file_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'dataset', 'movie_metadata.csv')
        
    print("Loading dataset...")
    df = pd.read_csv(file_path)
    
    # Select relevant columns
    cols = ['movie_title', 'genres', 'director_name', 'actor_1_name', 
            'plot_keywords', 'title_year', 'imdb_score', 'language', 'duration', 'movie_imdb_link']
    
    df = df[cols].copy()
    
    # Cleaning titles
    df['movie_title'] = df['movie_title'].apply(clean_title)
    
    # Handling missing values
    df['genres'] = df['genres'].fillna('')
    df['director_name'] = df['director_name'].fillna('Unknown')
    df['actor_1_name'] = df['actor_1_name'].fillna('Unknown')
    df['plot_keywords'] = df['plot_keywords'].fillna('')
    df['title_year'] = df['title_year'].fillna(0).astype(int)
    df['imdb_score'] = df['imdb_score'].fillna(0.0)
    
    # Process genres and keywords for soup
    df['genres'] = df['genres'].str.replace('|', ' ')
    df['plot_keywords'] = df['plot_keywords'].str.replace('|', ' ')
    
    # Create feature soup for TF-IDF
    def create_soup(x):
        return f"{x['genres']} {x['plot_keywords']} {x['director_name']} {x['actor_1_name']}"
    
    df['soup'] = df.apply(create_soup, axis=1)
    df['soup'] = df['soup'].str.lower()
    
    # Drop duplicates
    df = df.drop_duplicates(subset=['movie_title', 'title_year'])
    
    print(f"Preprocessed {len(df)} movies.")
    return df

if __name__ == "__main__":
    df = preprocess_data()
    # Save a sample to verify
    df.to_csv('dataset/processed_movies.csv', index=False)
    print("Processed data saved to dataset/processed_movies.csv")
