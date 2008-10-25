from django.contrib.comments.templatetags.comments import BaseCommentNode, CommentListNode
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import mptt_comments

register = template.Library()

class BaseMpttCommentNode(BaseCommentNode):
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, as_varname=None, comment=None):
        super(BaseMpttCommentNode, self). __init__(ctype=ctype, object_pk_expr=object_pk_expr, object_expr=object_expr, as_varname=as_varname, comment=comment)
        self.comment_model = mptt_comments.get_model()
    
    def get_root_node(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        return self.comment_model.objects.get_root_comment(ctype, object_pk)
        
class MpttCommentFormNode(BaseMpttCommentNode):
    """Insert a form for the comment model into the context."""
            
    def get_form(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk:
            return mptt_comments.get_form()(ctype.get_object_for_this_type(pk=object_pk), parent_comment=self.get_root_node(context))
        else:
            return None

    def render(self, context):
        context[self.as_varname] = self.get_form(context)
        return ''

class MpttCommentListNode(BaseMpttCommentNode):

    limit = 5
    cutoff_level = 3
    bottom_level = -1
    
    def get_query_set(self, context):
        qs = super(MpttCommentListNode, self).get_query_set(context)
        root_node = self.get_root_node(context)
        return qs.filter(tree_id=root_node.tree_id, level__gte=1, level__lte=self.cutoff_level).order_by('tree_id', 'lft')
        
    def get_context_value_from_queryset(self, context, qs):
        return list(qs[:self.limit])
        
    def render(self, context):
        qs = self.get_query_set(context)
        context[self.as_varname] = self.get_context_value_from_queryset(context, qs)
        context['comments_remaining'] = self.get_query_set(context).count() - self.limit
        context['root_comment'] = self.get_root_node(context)
        context['cutoff_level'] = self.cutoff_level
        context['bottom_level'] = self.bottom_level
        return ''        
        
def get_mptt_comment_list(parser, token):
    """
    Gets the list of comments for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_comment_list for [object] as [varname]  %}
        {% get_comment_list for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_comment_list for event as comment_list %}
        {% for comment in comment_list %}
            ...
        {% endfor %}

    """
    return MpttCommentListNode.handle_token(parser, token)


def get_mptt_comment_form(parser, token):
    """
    Get a (new) form object to post a new comment.

    Syntax::

        {% get_comment_form for [object] as [varname] %}
        {% get_comment_form for [app].[model] [object_id] as [varname] %}
    """
    return MpttCommentFormNode.handle_token(parser, token)


def mptt_comment_form_target():
    """
    Get the target URL for the comment form.

    Example::

        <form action="{% comment_form_target %}" method="POST">
    """
    return mptt_comments.get_form_target()

def children_count(comment):
    return (comment.rght - comment.lft) / 2

def mptt_comments_media():

    return mark_safe( render_to_string( ('comments/comments_media.html',) , { }) )
    
def display_comment_toplevel_for(target):

    model = target.__class__
        
    template_list = [
        "comments/%s_%s_display_comments_toplevel.html" % tuple(str(model._meta).split(".")),
        "comments/%s_display_comments_toplevel.html" % model._meta.app_label,
        "comments/display_comments_toplevel.html"
    ]
    return render_to_string(
        template_list, {
            "object" : target
        } 
        # RequestContext(context['request'], {})
    )
    
register.filter(children_count)
register.tag(get_mptt_comment_form)
register.simple_tag(mptt_comment_form_target)
register.simple_tag(mptt_comments_media)
register.tag(get_mptt_comment_list)
register.simple_tag(display_comment_toplevel_for)
