from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns as contrib_comments_urlpatterns
from django.conf import settings

urlpatterns = patterns('mptt_comments.views',
    url(r'^new/(\d+)/$',
        'new_comment',
        name='new-comment'
    ),
    url(r'^reply/(\d+)/$',
        'new_comment',
        name='comment-reply'
    ),
    url(r'^post/$',
        'post_comment',
        name='comments-post-comment'
    ),
    url(r'^posted-ajax/$',
        'comment_done_ajax',
        name='comments-comment-done-ajax'
    ),
    url(r'^more/(\d+)/$',
        'comments_more',
        name='comments-more'
    ),
    url(r'^get/(\d+)/$',
        'comments_subtree',
        name='comments-subtree'
    )
)

urlpatterns += contrib_comments_urlpatterns
