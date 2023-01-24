import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Follow

FIRST_POST = 0
POST_AMOUNT_ON_PAGE = 10
INDEX = reverse('posts:index')
POST_CREATE = reverse('posts:post_create')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_author = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            group=cls.group
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL - адрес использует соотвутствующий шаблон."""
        template_pages_names = {
            INDEX: 'posts/index.html',
            self.GROUP_LIST: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            POST_CREATE: 'posts/create_post.html',
            self.POST_EDIT: 'posts/create_post.html',
        }

        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX)
        response_post = response.context.get('page_obj').object_list[0]
        context_first_post = response.context['page_obj'][FIRST_POST]
        self.assertEqual(context_first_post, self.post)
        self.assertEqual(response_post.image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.GROUP_LIST)
        response_post = response.context.get('page_obj').object_list[0]
        expected = list(
            Post.objects.select_related('group'[:POST_AMOUNT_ON_PAGE])
        )
        self.assertEqual(list(response.context['page_obj']), expected)
        self.assertEqual(response_post.image, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.PROFILE)
        response_post = response.context.get('page_obj').object_list[0]
        expected = list(
            Post.objects.select_related('author')[:POST_AMOUNT_ON_PAGE]
        )
        self.assertEqual(list(response.context['page_obj']), expected)
        self.assertEqual(response_post.image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_DETAIL)
        response_post = response.context.get('post')

        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response_post.image, self.post.image)

    def test_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE)

        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.models.ModelChoiceField)
        )

        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_form_post_create_edit_correct_context(self):
        """Шаблон form_post_create и edit
        сформированы с правильным контекстом."""
        response = self.author_client.get(self.POST_EDIT)

        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.models.ModelChoiceField)
        )

        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """
        Проверка добавления поста на главную страницу,
        выбранной группы и в профиль пользователя.
        """
        form_fields = {
            INDEX: Post.objects.get(group=self.post.group),
            self.GROUP_LIST: Post.objects.get(group=self.post.group),
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_fields = response.context['page_obj']
                self.assertIn(expected, form_fields)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверка на появление созданного поста а чужой группе."""
        form_fields = {
            self.GROUP_LIST: Post.objects.exclude(group=self.post.group),
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_fields = response.context['page_obj']
                self.assertNotIn(expected, form_fields)

    def test_cache_index(self):
        """Проверка кэша. При удалении запись остается до очистки кэша."""
        posts1 = self.authorized_client.get(INDEX).content
        Post.objects.filter(id=1).delete()
        posts2 = self.authorized_client.get(INDEX).content
        self.assertTrue(posts1 == posts2)
        cache.clear()
        posts3 = self.authorized_client.get(INDEX).content
        self.assertFalse(posts1 == posts3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user1')
        cls.user_following = User.objects.create_user(username='user2')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст'
        )
        cls.FOLLOW_INDEX = reverse('posts:follow_index')
        cls.FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_following}
        )
        cls.UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_following}
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_follow(self):
        """Зарегистрированный пользователь может подписаться на автора."""
        follower_count = Follow.objects.count()
        self.follower_client.get(self.FOLLOW)
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(self.UNFOLLOW)
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_will_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = self.post
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(self.FOLLOW_INDEX)
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response2 = self.follower_client.get(self.FOLLOW_INDEX)
        self.assertEqual(len(response2.context['page_obj']), 0)
