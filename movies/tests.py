from django.test import TestCase
from django.urls import reverse

from movies.models import Comment, Movies
from users.models import User


class MovieCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")
        self.movie = Movies.objects.create(
            tvdb_id=1, name="Test Movie", slug="test-movie",
        )

    def test_active_comment_visible_inactive_hidden(self):
        Comment.objects.create(
            person=self.user, movies=self.movie, comment="عالی بود", is_active=True,
        )
        Comment.objects.create(
            person=self.user, movies=self.movie, comment="اسپم", is_active=False,
        )
        resp = self.client.get(reverse("movie_detail", args=["test-movie"]))
        self.assertContains(resp, "عالی بود")
        self.assertNotContains(resp, "اسپم")

    def test_authenticated_post_creates_comment(self):
        self.client.login(username="alice", password="pw")
        resp = self.client.post(
            reverse("movie_comment", args=["test-movie"]), {"comment": "خیلی خوب بود"}
        )
        self.assertEqual(resp.status_code, 200)
        c = Comment.objects.get(movies=self.movie)
        self.assertEqual(c.comment, "خیلی خوب بود")
        self.assertEqual(c.person, self.user)
        self.assertTrue(c.is_active)

    def test_blank_comment_rejected(self):
        self.client.login(username="alice", password="pw")
        resp = self.client.post(
            reverse("movie_comment", args=["test-movie"]), {"comment": "   "}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_anonymous_post_redirects(self):
        resp = self.client.post(
            reverse("movie_comment", args=["test-movie"]), {"comment": "نظر"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)
