# -*- coding: utf-8 -*-
import logging

import time
import datetime
# from django.core.urlresolvers import reverse
from django.conf import settings
from api import validate_api_call, fetch_url, rest_request, decode_request
from django.http import HttpResponse, HttpResponseRedirect
from admin.models import User, Subject, UserSubject, Photo
import simplejson as json

from admin import R


@validate_api_call
def daily(request):
    """aktualny temat + dane usera"""

    subject = Subject.objects.get_current()
    if subject is None:
        logging.error('Cannot find currect subject')
        self.response.set_status(500)
        return HttpResponse('Error')

    return HttpResponse(json.dumps({
        'subject': subject.to_dict(),
        'user': request.user.to_dict(),
    }))


@validate_api_call
def vote(request):
    """pobierz losowe fotki do glosowania (tylko jeszcze nie glosowane)"""

    if request.method == 'POST':
        """glosuj"""

        redis = R()

        if request.POST.get('media_id') == None:
            logging.info('no media id')
            return HttpResponse('Error')

        try:
            media_id = request.POST['media_id']
        except ValueError:
            logging.error('%s is not valid instagram_id' % request.POST.get('media_id'))
            redis.add_photo(request.POST.get('media_id'))
            return HttpResponse('invalid instagram id')

        if request.POST.get('type') == 'like':
            rest_request('/api/instagram/',
                         {'type': 'like', 'media_id': media_id, 'user': request.user.name, 'token': request.user.token})
        elif request.POST.get('type') == 'unlike':
            rest_request('/api/instagram/', {'type': 'unlike', 'media_id': media_id, 'user': request.user.name,
                                             'token': request.user.token})
        else:
            logging.info('unregocognized type=%s' % request.GET.get('type'))

        return HttpResponse('ok')

    photos = Photo.objects.get_more_photos(request.user)

    return HttpResponse(json.dumps({
        'photos': photos
    }))


@validate_api_call
def photos(request):
    """lista fotek w biezacym temacie"""

    if request.method == 'POST':
        """operacje na moich zdjeciach"""

        if request.GET.get('media_id') == None:
            logging.info('no media id')
            return HttpResponse('Error')

        try:
            media_id = request.GET.get('media_id')
        except ValueError:
            logging.error('%s is not valid instagram_id' % request.GET.get('media_id'))
            return

        if request.GET.get('type') == 'activate':
            p = Photo.objects.get_by_instagram_id(media_id)
            if p is not None:
                p.is_active = True
                p.is_user_active = True
                p.put()
            # logging.info('activated %s' % media_id)
            else:
                rest_request('/api/instagram/',
                             {'type': 'add_instadaily_tag', 'media_id': media_id, 'user': request.user.name,
                              'token': request.user.token})

        elif request.GET.get('type') == 'deactivate':
            p = Photo.objects.get_by_instagram_id(media_id)
            if p is not None:
                p.is_user_active = False
                p.put()
            # logging.info('deactivated %s' % media_id)
            else:
                logging.warning('cannot deactivate unavailable photo')

        else:
            logging.info('unregocognized type=%s' % request.GET.get('type'))

        return HttpResponse('ok')

    subject = Subject.objects.get_current()

    photos = Photo.objects.filter(user=request.user.name, subject=subject, is_active=True).order_by('date_instagram')

    blocked = []
    fetched_ids = []
    ps = {'active': [], 'inactive': []}
    for p in photos:
        fetched_ids.append(p.instagram_id)

        if p.is_blocked:
            continue
        if p.is_active and p.is_user_active:
            ps['active'].append(p.to_dict())
        else:
            ps['inactive'].append(p.to_dict())

    # get latest photos from instagram
    url = 'https://api.instagram.com/v1/users/%s/media/recent/?access_token=%s&min_timestamp=%s&max_timestamp=%s' % (
    request.user.instagram_id, request.user.access_token, int(time.mktime(subject.active_from.utctimetuple())),
    int(time.mktime(subject.active_to.utctimetuple())))

    try:
        data = json.loads(fetch_url(url))
    except Exception, e:
        return HttpResponse(json.dumps({
            'photos': ps
        }))

    # TODO: pagination

    if not data.has_key('data'):
        logging.error('No data in fetched url: %s' % url)
        return HttpResponse(json.dumps({
            'photos': ps
        }))

    for photo in data['data']:
        if photo['id'] in fetched_ids: continue
        d = datetime.datetime.fromtimestamp(float(photo['created_time']))
        if d < subject.active_from or d > subject.active_to: continue
        # logging.info('%s < %s > %s' % (str(d), str(subject.active_from), str(subject.active_to)))

        p = Photo().to_dict(photo)
        if p['active'] and ['user_active']:
            Photo().add_or_update(photo)
            ps['active'].append(p)
        else:
            ps['inactive'].append(p)

    return HttpResponse(json.dumps({
        'photos': ps
    }))


@validate_api_call
def subjects(request, subject_id):
    """lista tematow w ktorych bral udzial user"""

    subjects = []

    current_best_photo = Photo.objects.filter(user=request.user.name, subject=Subject.objects.get_by_id(subject_id),
                                              is_active=True, is_user_active=True, is_blocked=False).order_by(
        '-total_score').get()
    if current_best_photo:
        current_best_photo = current_best_photo.to_dict()

    subjects.append({
        'subject': current_subject.to_dict(),
        'best_photo': current_best_photo,
        'points': 0
    })
    for us in UserSubject.objects.get_by_user(request.user.name):
        subjects.append(us.to_dict())

    return HttpResponse(json.dumps({
        'subjects': subjects
    }))


@validate_api_call
def subjects_for_user(request, username=None, subject_id=None):
    """lista tematow w ktorych bral udzial user"""

    subjects = []

    if username == None:
        username = reuqest.user.name

    if subject_id == None:
        subject = Subject.objects.get_current()
    else:
        subject = Subject.objects.get_by_id(subject_id)

    try:
        current_best_photo = Photo.objects.filter(user=username, subject=subject, is_active=True, is_user_active=True,
                                                  is_blocked=False).order_by('-total_score')[0]
        current_best_photo = current_best_photo.to_dict()
    except Photo.DoesNotExist:
        current_best_photo = None
    except Exception, e:
        current_best_photo = None

    subjects.append({
        'subject': Subject.objects.get_current().to_dict(),
        'best_photo': current_best_photo,
        'points': 0
    })

    for us in UserSubject.objects.get_by_user(username):
        subjects.append(us.to_dict())

    return HttpResponse(json.dumps({
        'subjects': subjects
    }))


@validate_api_call
def subjects(request):
    """lista fotek usera dla danego tematu, sortowane po punktach"""

    photos = []
    for photo in Photo.objects.filter(user=request.user.name, subject=Subject.objects.get_current(), is_active=True,
                                      is_user_active=True, is_blocked=False).order_by('-total_score'):
        photos.append(photo.to_dict())

    return HttpResponse(json.dumps({
        'photos': photos
    }))


@validate_api_call
def subject_for_user(request, subject_id, username):
    """lista fotek usera dla danego tematu, sortowane po punktach"""

    photos = []
    for photo in Photo.objects.filter(user=username, subject=Subject.objects.get_by_id(int(subject_id)), is_active=True,
                                      is_user_active=True, is_blocked=False).order_by('-total_score'):
        photos.append(photo.to_dict())

    return HttpResponse(json.dumps({
        'photos': photos
    }))


@validate_api_call
def leaderboard(request):
    def _dict(scores, pos_start, year=0, month=0):

        data = []
        for s in scores:
            data.append({
                'user': User.objects.get_by_name(s[0]).to_dict(),
                'points': s[1],
                'position': pos_start,
                'position_change': 0,
                'month': month,
                'year': year
            })
            pos_start += 1

        return data

    redis = R()
    users = {'month': [], 'overall': []}

    # --- OVERALL

    pos = redis.r.zrevrank('leaderboard', request.user.name)

    if pos is None or pos <= 8 or request.user.points == 0:
        users['overall'] = _dict(redis.r.zrevrange('leaderboard', 1, 15, withscores=True), 1)
    else:
        users['overall'].extend(_dict(redis.r.zrevrange('leaderboard', 1, 3, withscores=True), 1))
        users['overall'].extend(_dict(redis.r.zrevrange('leaderboard', pos - 5, pos + 7, withscores=True), pos - 5))

    # --- MONTHLY

    month, year = datetime.datetime.now().month, datetime.datetime.now().year
    key = 'leaderboard:year:%d:month:%d' % (year, month)
    pos = redis.r.zrevrank(key, request.user.name)

    if pos is None or pos <= 8 or request.user.points == 0:
        users['month'] = _dict(redis.r.zrevrange('leaderboard', 1, 15, withscores=True), 1, month, year)
    else:
        users['month'].extend(_dict(redis.r.zrevrange('leaderboard', 1, 3, withscores=True), 1, month, year))
        users['month'].extend(
            _dict(redis.r.zrevrange('leaderboard', pos - 5, pos + 7, withscores=True), pos - 5, month, year))

    if settings.DEBUG:
        print json.dumps({
            'leaderboard': {
                'month': users['month'],
                'overall': users['overall']
            }
        })

    return HttpResponse(json.dumps({
        'leaderboard': {
            'month': users['month'],
            'overall': users['overall']
        }
    }))
