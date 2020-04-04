from django import template
from rest_framework.renderers import HTMLFormRenderer
register = template.Library()

# @register.simple_tag
# def render_form(serializer, template_pack=None):
#     style = {'template_pack': template_pack} if template_pack else {}
#     renderer = HTMLFormRenderer()
#     return renderer.render(serializer.data, None, {'style': style})

@register.simple_tag
def debugDictObject(a1):
  print(a1.__dict__)
  return ''

@register.simple_tag
def debugField(a1):
  print(a1._field.__dict__)
  return ''
# environment.filters['debug']=debug