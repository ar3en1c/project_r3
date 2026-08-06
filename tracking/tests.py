from django.test import TestCase
from django.urls import reverse

from movies.models import Movies
from series.models import Series
from tracking.models import Track
from users.models import User


class FavoritesViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")
        self.series = Series.objects.create(
            tvdb_id=1, name="Test Series", slug="test-series", episode_count=10,
        )
        self.movie = Movies.objects.create(
            tvdb_id=1, name="Test Movie", slug="test-movie",
        )
        self.client.login(username="alice", password="pw")

    def _fav(self, typeOfWatch, **fk):
        return Track.objects.create(
            user=self.user, typeOfWatch=typeOfWatch, favorite=True, **fk)

    def test_favorites_page_lists_only_favorites(self):
        self._fav("Series", serial=self.series)
        self._fav("Movie", movies=self.movie)
        # non-favorite should not appear
        Track.objects.create(user=self.user, typeOfWatch="Movie",
                             movies=Movies.objects.create(
                                 tvdb_id=2, name="Other", slug="other"),
                             favorite=False)
        resp = self.client.get(reverse("tracking:favorites"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Test Series", html)
        self.assertIn("Test Movie", html)
        self.assertNotIn(">Other<", html)

    def test_remove_favorite_unflags_and_response_reflects(self):
        self._fav("Series", serial=self.series)
        resp = self.client.post(
            reverse("tracking:remove_favorite"),
            {"type": "series", "slug": "test-series"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Track.objects.get(user=self.user, serial=self.series).favorite)
        # refreshed panel no longer contains it
        self.assertNotIn("Test Series", resp.content.decode())

    def test_remove_favorite_requires_login(self):
        url = reverse("tracking:remove_favorite")
        self.client.logout()
        resp = self.client.post(url, {"type": "series", "slug": "test-series"})
        self.assertNotEqual(resp.status_code, 200)
