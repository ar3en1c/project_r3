from django.test import TestCase
from django.urls import reverse

from movies.models import Movies
from series.models import Series
from tracking.models import Track
from users.models import User


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")
        self.series = Series.objects.create(
            tvdb_id=1, name="Test Series", slug="test-series", episode_count=10,
        )
        self.movie = Movies.objects.create(
            tvdb_id=1, name="Test Movie", slug="test-movie",
        )
        self.client.login(username="alice", password="pw")

    def test_profile_page_renders_both_panels(self):
        Track.objects.create(user=self.user, typeOfWatch="Series",
                             serial=self.series, status="watching", progress=3)
        Track.objects.create(user=self.user, typeOfWatch="Movie",
                             movies=self.movie, status="plan to watch")
        resp = self.client.get(reverse("users:profile"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        # both tabs present with their serialized data
        self.assertIn('id="series-panel"', html)
        self.assertIn('id="movie-panel"', html)
        self.assertIn("در حال تماشا", html)

    def test_series_step_increments_and_completes(self):
        Track.objects.create(user=self.user, typeOfWatch="Series",
                             serial=self.series, status="watching", progress=0)
        # up to last episode -> complete
        self.client.post(reverse("users:series_step", args=["test-series"]),
                         {"delta": 10})
        t = Track.objects.get(user=self.user, serial=self.series)
        self.assertEqual(t.progress, 10)
        self.assertEqual(t.status, "completed")
        # back down from completed -> watching
        self.client.post(reverse("users:series_step", args=["test-series"]),
                         {"delta": -1})
        t.refresh_from_db()
        self.assertEqual(t.progress, 9)
        self.assertEqual(t.status, "watching")

    def test_movie_stage_changes_status(self):
        Track.objects.create(user=self.user, typeOfWatch="Movie",
                             movies=self.movie, status="plan to watch")
        self.client.post(reverse("users:movie_stage", args=["test-movie"]),
                         {"status": "completed"})
        t = Track.objects.get(user=self.user, movies=self.movie)
        self.assertEqual(t.status, "completed")

    def test_rate_and_clear(self):
        Track.objects.create(user=self.user, typeOfWatch="Series",
                             serial=self.series, status="watching")
        self.client.post(reverse("users:rate"),
                         {"type": "series", "slug": "test-series", "rate": 8})
        t = Track.objects.get(user=self.user, serial=self.series)
        self.assertEqual(t.user_rate, 8)
        # rating 0 clears it
        self.client.post(reverse("users:rate"),
                         {"type": "series", "slug": "test-series", "rate": 0})
        t.refresh_from_db()
        self.assertIsNone(t.user_rate)
