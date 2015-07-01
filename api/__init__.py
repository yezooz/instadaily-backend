# -*- coding: utf-8 -*-
import hashlib
from urllib import urlencode
from httplib2 import Http
# import datetime, time
from django.conf import settings
from django.http import HttpResponseBadRequest
from functools import wraps
from admin.models import User
# import simplejson as json

SECRET = 'be36e27ab19547409afcd23ef388b903'


def fetch_url(url):
    response = urllib2.urlopen(url)
    # code = response.code
    # headers = response.headers
    contents = response.read()

    return contents


def rest_request(url, data=[], method='POST'):
    if url.startswith('/'):
        url = '%s%s' % (settings.SITE_ROOT_URL, url[1:])

    h = Http(disable_ssl_certificate_validation=True)
    resp, content = h.request(url, method, urlencode(data))

    return content


def encode_request(request):
    if request.method == 'POST':
        user = User.objects.get_by_id(int(request.POST['user_id']))
    else:
        user = User.objects.get_by_id(int(request.GET['user_id']))

    res = []
    par = {}
    for param in request.query_string.split('&'):
        param, value = param.split('=')
        if param == 'token': continue
        res.append('%s=%s' % (param, value))
        par[param] = value

    md5 = hashlib.md5()
    # print '%s%s%s' % ('&'.join(res), user.secret_key, SECRET)
    md5.update('%s%s%s' % ('&'.join(res), user.secret_key, SECRET))
    par['token'] = md5.hexdigest()
    return par


def validate_request(request):
    # check required values
    try:
        if request.method == 'POST':
            req_token = request.POST['token']
            req_user = request.POST['user']
        else:
            req_token = request.GET['token']
            req_user = request.GET['user']
        if len(req_token) != 32 or len(req_user) == 0:
            raise TypeError
    except (ValueError, TypeError):
        return False

    # check user
    user = User.objects.get_by_name(req_user)
    if user is None:
        return False
    # print 'Calculated hash: %s | Received hash: %s' % (encode_request(request)['token'], req_token)
    # if encode_request(request)['token'] == req_token:
    if user.token == req_token:
        # print 'MATCHING'
        return True
    else:
        # print 'NOT MATCHING'
        return False


def decode_request(request):
    if not validate_request(request):
        return None

    res = {}
    if request.method == 'POST':
        res['user'] = User.objects.get_by_name(request.POST['user'])
    else:
        res['user'] = User.objects.get_by_name(request.GET['user'])

    # for param in request.query_string.split('&'):
    # 	param, value = param.split('=')
    # 	res[param] = value

    return res


def validate_api_call(func):
    def _check(self, *args, **kwargs):
        decoded = decode_request(self)
        if decoded is None:
            return HttpResponseBadRequest('Invalid request')
        self.user = decoded['user']

        return func(self, *args, **kwargs)

    return wraps(func)(_check)
