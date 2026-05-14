import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class MovieRecommender:
    def __init__(self, processed_df):
        self.df = processed_df.reset_index(drop=True)
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['soup'])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        
    def get_recommendations(self, title, top_k=10):
        # Find index of movie
        try:
            idx = self.df[self.df['movie_title'].str.lower() == title.lower()].index[0]
        except IndexError:
            return pd.DataFrame()
        
        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        
        # Sort by similarity
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top indices (excluding self)
        sim_indices = [i[0] for i in sim_scores[1:top_k+1]]
        
        recommendations = self.df.iloc[sim_indices].copy()
        recommendations['similarity_score'] = [i[1] for i in sim_scores[1:top_k+1]]
        
        # Apply metadata weighting (boost higher rated/recent movies slightly)
        # score = similarity * 0.7 + (rating/10) * 0.2 + (year_norm) * 0.1
        current_year = 2026
        recommendations['year_boost'] = (recommendations['title_year'] - 1900) / (current_year - 1900)
        recommendations['final_score'] = (
            recommendations['similarity_score'] * 0.7 + 
            (recommendations['imdb_score'] / 10.0) * 0.2 + 
            recommendations['year_boost'] * 0.1
        )
        
        return recommendations.sort_values(by='final_score', ascending=False)

    def search_movies(self, query):
        if not query:
            return pd.DataFrame()
        return self.df[self.df['movie_title'].str.contains(query, case=False, na=False)].head(10)

    def get_top_rated(self, n=10):
        return self.df.sort_values(by='imdb_score', ascending=False).head(n)

    def get_trending(self, n=10):
        # Trending = High rating + recent
        return self.df[self.df['title_year'] >= 2010].sort_values(by='imdb_score', ascending=False).head(n)

    def get_genre_distribution(self):
        # Split genres and count
        all_genres = self.df['genres'].str.split(expand=True).stack()
        return all_genres.value_counts().head(10)

    def get_yearly_trends(self):
        # Average rating by year (recent 20 years)
        recent_df = self.df[self.df['title_year'] > 2000]
        return recent_df.groupby('title_year')['imdb_score'].mean()

    def get_top_directors(self):
        # Directors with highest average rating (min 3 movies)
        dir_stats = self.df.groupby('director_name').agg(
            count=('movie_title', 'count'),
            avg_rating=('imdb_score', 'mean')
        )
        return dir_stats[dir_stats['count'] >= 3].sort_values('avg_rating', ascending=False).head(10)
        
    def get_mood_recommendations(self, mood, n=10):
        mood_mapping = {
            'Action-Packed': ['action', 'thriller', 'adventure', 'spy', 'fight'],
            'Feel Good': ['comedy', 'romance', 'family', 'animation', 'happy'],
            'Dark & Gritty': ['crime', 'horror', 'mystery', 'murder', 'dark'],
            'Mind-Bending': ['sci-fi', 'fantasy', 'time travel', 'puzzle', 'space']
        }
        
        keywords = mood_mapping.get(mood, [])
        if not keywords:
            return pd.DataFrame()
            
        # Create a mock query using keywords
        query = " ".join(keywords)
        query_vec = self.vectorizer.transform([query])
        sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        sim_scores = list(enumerate(sim))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_indices = [i[0] for i in sim_scores[:n]]
        
        return self.df.iloc[sim_indices]
