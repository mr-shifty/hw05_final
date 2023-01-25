import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm, CommentForm
from posts.models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
CREATE_POST = reverse('posts:post_create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_guest = User.objects.create_user(username='guest')
        cls.user_author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
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

        cls.form = PostForm()

        cls.comment_form = CommentForm()

        cls.POST_EDIT = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )

        cls.ADD_COMMENTS = reverse(
            'posts:add_comment',
            args={cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user_guest)
        self.author_client.force_login(self.post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Пост."""
        posts_count = Post.objects.all().count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'author': self.user_author.id,
            'image': uploaded
        }

        response = self.author_client.post(
            CREATE_POST,
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        posts = Post.objects.exclude(id=self.post.id)
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user_author)
        self.assertEqual(post.image, self.post.image)
        self.assertRedirects(response, self.PROFILE)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Пост."""
        posts_count = Post.objects.all().count()
        form_data = {
            'group': self.group.id,
            'author': self.user_author.id,
            'text': 'Тест текст',
        }

        response = self.author_client.post(
            self.POST_EDIT,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.author, self.user_author)
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_edited_authorized_user(self):
        """Комментировать посты может только авторизованный пользователь."""
        comments_count = Comment.objects.all().count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.guest_client.post(
            self.ADD_COMMENTS,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Post.objects.filter(
                text=self.post.text,
                comments=1
            ).exists()
        )

    def test_comment_post(self):
        """
        После успешной отпраки комментарий появляется на странице поста.
        """
        comments_count = Comment.objects.all().count()
        form_data = {
            'post': self.post,
            'author': self.user_author.id,
            'text': 'Тестовый текст'
        }

        response = self.authorized_client.post(
            self.ADD_COMMENTS,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                comments=1
            ).exists()
        )
