from django.test import TestCase
from django.urls import reverse

from series.models import Comment, Series
from users.models import User


class SeriesCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw")
        self.series = Series.objects.create(
            tvdb_id=1, name="Test Series", slug="test-series", episode_count=10,
        )

    def test_active_comment_visible_inactive_hidden(self):
        Comment.objects.create(
            person=self.user, series=self.series, comment="عالی بود", is_active=True,
        )
        Comment.objects.create(
            person=self.user, series=self.series, comment="اسپم", is_active=False,
        )
        resp = self.client.get(reverse("series:series_detail", args=["test-series"]))
        self.assertContains(resp, "عالی بود")
        self.assertNotContains(resp, "اسپم")

    def test_authenticated_post_creates_comment(self):
        self.client.login(username="alice", password="pw")
        resp = self.client.post(
            reverse("series:series_comment", args=["test-series"]), {"comment": "خیلی خوب بود"}
        )
        self.assertEqual(resp.status_code, 200)
        c = Comment.objects.get(series=self.series)
        self.assertEqual(c.comment, "خیلی خوب بود")
        self.assertEqual(c.person, self.user)
        self.assertTrue(c.is_active)

    def test_blank_comment_rejected(self):
        self.client.login(username="alice", password="pw")
        resp = self.client.post(
            reverse("series:series_comment", args=["test-series"]), {"comment": "   "}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_anonymous_post_redirects(self):
        resp = self.client.post(
            reverse("series:series_comment", args=["test-series"]), {"comment": "نظر"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)
