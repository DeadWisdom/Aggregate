from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings

def render(request, template, dict):
    dict['MEDIA_URL'] = settings.MEDIA_URL
    dict['SITE_TITLE'] = settings.SITE_TITLE
    dict['request'] = request
    return render_to_response(template, dict)

