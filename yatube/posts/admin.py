from django.contrib import admin

from .models import Group, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pub_date',
        'pk',
        'text',
        'author',
        'group'
    )
    list_filter = ('pub_date',)
    list_editable = ('group',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'author', 'text')
    search_fields = ('text',)
    list_filter = ('author',)
    empty_value_display = '-пусто-'


admin.site.register(Group)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
