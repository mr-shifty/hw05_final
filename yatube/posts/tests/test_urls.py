from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

INDEX = reverse('posts:index')
POST_CREATE = reverse('posts:post_create')
UNEXISTING = '/unexisting_page/'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_author = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

        cls.GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.user_author)

    def test_urs_exists_at_desired_location_guest(self):
        """Проверка доступа на станицы, авторизированного пользователя и
        гостя."""
        templates_url_names = (
            (INDEX, self.guest_client, HTTPStatus.OK),
            (self.GROUP_LIST, self.guest_client, HTTPStatus.OK),
            (self.PROFILE, self.guest_client, HTTPStatus.OK),
            (self.POST_DETAIL, self.guest_client, HTTPStatus.OK),
            (POST_CREATE, self.guest_client, HTTPStatus.FOUND),
            (POST_CREATE, self.author_client, HTTPStatus.OK),
            (self.POST_EDIT, self.author_client, HTTPStatus.OK),
            (self.POST_EDIT, self.guest_client, HTTPStatus.FOUND),
        )
        for url, user, answer in templates_url_names:
            with self.subTest(url=url):
                self.assertEqual(user.get(url).status_code, answer)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (INDEX, 'posts/index.html'),
            (self.GROUP_LIST, 'posts/group_list.html'),
            (self.PROFILE, 'posts/profile.html'),
            (self.POST_DETAIL, 'posts/post_detail.html'),
            (POST_CREATE, 'posts/create_post.html'),
            (self.POST_EDIT, 'posts/create_post.html'),
        )

        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_task_detail_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /post/self.post.id/edit
        перенаправит пользователя не автора.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_custom_template_404(self):
        """Страница 404 отдаёт кастомный шаблон."""
        response = self.authorized_client.get(UNEXISTING)
        self.assertTemplateUsed(response, 'core/404.html')
