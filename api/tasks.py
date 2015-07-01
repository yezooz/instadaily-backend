# -*- coding: utf-8 -*-
import logging
import hashlib

import time
# from django.core.urlresolvers import reverse
# from django.conf import settings
from api import validate_api_call, rest_request, decode_request
from django.http import HttpResponse, HttpResponseRedirect
from admin.models import User, Subject, Photo
import simplejson as json

INSTADAILY_TAG_MSG = "#instadaily%20-%20this%20is%20a%20photo%20I%20made%20to%20win%20against%20other%20Instagrammers%2C%20join%20the%20competition!%20instadailyapp.com"


@validate_api_call
def APICallWorker(request):
    if request.method == 'GET': return HttpResponse('Method not supported')

    # --- Validation
    req = decode_request(request)
    if req is None:
        logging.warning('unauthorized query - ignoring')
        return HttpResponse('ignored')

    if request.POST.get('type') == None:
        logging.warning('added task without required params - ignoring')
        return HttpResponse('ignored')

    # --- Methods
    url = 'https://api.instagram.com/v1'
    method = 'GET'
    params = {}

    if request.POST.get('type') == 'like':
        method = 'POST'
        params = {'access_token': req['user'].access_token}
        url += '/media/%s/likes/' % request.POST.get('media_id')

    elif request.POST.get('type') == 'unlike':
        method = 'DELETE'
        url += '/media/%s/likes/' % request.POST.get('media_id')
        url += '?access_token=' + req['user'].access_token

    elif request.POST.get('type') == 'add_instadaily_tag':
        method = 'POST'
        params = 'access_token=%s&text=%s' % (req['user'].access_token, INSTADAILY_TAG_MSG)
        url += '/media/%s/comments' % request.POST.get('media_id')

    elif request.POST.get('type') == 'user' and request.POST.has_key('user_id'):
        url += '/users/%s' % request.POST.get('user_id')
        url += '?access_token=' + req['user'].access_token

    result = rest_request(url, params, method)

    if request.POST.get('type') == 'like':
        p = Photo.objects.get_by_instagram_id(request.POST.get('media_id'))
        p.likes += 1
        p.save()

        req['user'].vote_like += 1
        req['user'].save()

    elif request.POST.get('type') == 'user' and request.POST.get('user_id') is not None:
        try:
            data = json.loads(result)['data']
        except json.JSONDecodeError:
            print 'failed to decode json %s' % result
            print url
            return HttpResponse('')
        except KeyError:
            logging.error('DATA not found in recent photos for user %s' % request.POST.get('user_id'))
            return HttpResponse('')

        try:
            user = User.objects.filter(instagram_id=data['id']).get()
            user.pic = data['profile_picture']
            user.full_name = data['full_name']
            user.save()

        except User.DoesNotExist:
            user = User()
            user.name = data['username']
            user.instagram_id = data['id']
            user.full_name = data['full_name']
            user.pic = data['profile_picture']
            user.photos = 0
            user.vote_like = 0
            user.vote_dislike = 0
            try:
                user.last_subject_id = Subject.objects.get_current().id
            except AttributeError:
                logging.error('cannot find current subject!!!')
                user.last_subject_id = 0
            user.last_subject_points = 0
            user.save()

    else:
        try:
            j = json.loads(result)
        except json.JSONDecodeError:
            print 'failed to decode json %s' % result
            print url
            return HttpResponse('')

        # only disliking photos that wasn't previously liked
        if j.has_key('meta') and j['meta'].has_key('error_message') and j['meta'][
            'error_message'] == 'the user has not liked this media':
            p = Photo.objects.get_by_instagram_id(request.POST.get('media_id'))
            p.dislikes += 1
            p.save()

            req['user'].vote_dislike += 1
            req['user'].save()

            return HttpResponse('')

        # logging.warning('API call failed with %s' % result)

    return HttpResponse('')
