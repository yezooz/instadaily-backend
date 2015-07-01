# -*- coding: utf-8 -*-
# from django.core.urlresolvers import reverse
from annoying.decorators import render_to
from admin.models import Photo


@render_to('www/index.html')
def index(request):
    last_50 = Photo.objects.filter(is_active__exact=True, is_user_active__exact=True, is_blocked__exact=False).order_by(
        '-date_added')[:20]

    i = 0
    last_50 = [p for p in last_50]
    photos = []
    for x in xrange(0, len(last_50) / 2):
        photos.append([last_50[i], last_50[i + 1]])
        i += 2

    return {'photos': photos}
