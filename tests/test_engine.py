import unittest
import pandas as pd
from recommendation_engine import MovieRecommender

class TestRecommendationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a tiny mock dataset
        data = {
            'movie_title': ['Movie A', 'Movie B', 'Movie C', 'Movie D'],
            'genres': ['Action Sci-Fi', 'Action Thriller', 'Comedy', 'Action Sci-Fi'],
            'director_name': ['Dir 1', 'Dir 2', 'Dir 3', 'Dir 1'],
            'actor_1_name': ['Act 1', 'Act 2', 'Act 3', 'Act 1'],
            'plot_keywords': ['space alien', 'spy chase', 'funny joke', 'space alien mars'],
            'title_year': [2020, 2019, 2021, 2022],
            'imdb_score': [8.0, 7.5, 6.0, 8.5],
            'soup': [
                'action sci-fi space alien dir 1 act 1',
                'action thriller spy chase dir 2 act 2',
                'comedy funny joke dir 3 act 3',
                'action sci-fi space alien mars dir 1 act 1'
            ]
        }
        cls.df = pd.DataFrame(data)
        cls.recommender = MovieRecommender(cls.df)

    def test_search(self):
        results = self.recommender.search_movies('Movie A')
        self.assertFalse(results.empty)
        self.assertEqual(results.iloc[0]['movie_title'], 'Movie A')

    def test_recommendation_similarity(self):
        # Movie A and Movie D should be highly similar
        recs = self.recommender.get_recommendations('Movie A', top_k=1)
        self.assertEqual(recs.iloc[0]['movie_title'], 'Movie D')

if __name__ == '__main__':
    unittest.main()
