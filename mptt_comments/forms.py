from django.utils.encoding import force_unicode
from django.conf import settings
from django.contrib.comments import get_model
from django.contrib.comments.forms import CommentForm
from django.utils.translation import ugettext_lazy as _
from django import forms
import time
from mptt_comments.models import MpttComment

class MpttCommentForm(CommentForm):
    title = forms.CharField(label=_("Title"))
    parent_pk = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, target_object, parent_comment=None, data=None, initial=None):
        self.parent_comment = parent_comment
        super(MpttCommentForm, self).__init__(target_object, data=data, initial=initial)
        if self.should_title_be_forced():
            self.fields['title'].widget.attrs['readonly'] = True

        self.fields.keyOrder = [
            'title',
            'comment',
            'honeypot',
            'content_type',
            'object_pk',
            'timestamp',
            'security_hash',
            'parent_pk'
        ]

    def should_title_be_forced(self):
        return self.parent_comment and getattr(settings, 'MPTT_FORCE_TITLE_ON_REPLIES', False)

    def generate_title(self):
        if not self.parent_comment:
            return force_unicode(self.target_object)
        else:
            return u'%s%s' % ((self.parent_comment.title[:3] != u'Re:') and 'Re: ' or u'', self.parent_comment.title)

    def clean_title(self):
        if self.should_title_be_forced():
            self.cleaned_data['title'] = self.generate_title()

        # Truncates title to 255 chrs to avoid integrity errors
        return self.cleaned_data['title'][:255]

    def get_comment_model(self):
        """
        Get the comment model to create with this form. Subclasses in custom
        comment apps should override this, get_comment_create_data, and perhaps
        check_for_duplicate_comment to provide custom comment models.
        """
        return MpttComment

    def get_comment_create_data(self):
        """
        Returns the dict of data to be used to create a comment. Subclasses in
        custom comment apps that override get_comment_model can override this
        method to add extra fields onto a custom comment model.
        """

        data = super(MpttCommentForm, self).get_comment_create_data()
        parent_comment = None
        parent_pk = self.cleaned_data.get("parent_pk")
        if parent_pk:
            parent_comment = get_model().objects.get(pk=parent_pk)
        data.update({
            'user_name': '',
            'user_email': '',
            'user_url': '',
            'is_public': parent_comment and parent_comment.is_public or True,
            'title': self.cleaned_data["title"],
            'parent': parent_comment
        })

    def generate_security_data(self):
        """Generate a dict of security data for "initial" data."""
        timestamp = int(time.time())
        security_dict = {
            'content_type': str(self.target_object._meta),
            'object_pk': str(self.target_object._get_pk_val()),
            'timestamp': str(timestamp),
            'security_hash': self.initial_security_hash(timestamp),
            'parent_pk': self.parent_comment and str(self.parent_comment.pk) or '',
            'title': self.generate_title(),
            }

        return security_dict
