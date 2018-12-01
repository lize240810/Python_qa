from django.contrib.auth import logout
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from .forms import UserForm
from django.urls import reverse

import json


def register(request):
    registered = False
    
    if request.method == 'POST':
        ret = {}
        user_form = UserForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            ret = {
                'error': 0,
                'msg':'注册成功'
            }
            registered = True
        else:
            ret = {
                'error': 1,
                'msg':'注册失败'
            }

            # return render(request,
            #     'login.html',
            #     {'user_form': user_form, 'registered': registered})
        return HttpResponse(json.dumps(ret), content_type='application/json')
    else:
        user_form = UserForm()

    return render(request, 
        'login.html',
        {'user_form': user_form, 'registered': registered})


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        ret = {}
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # 如果帐户是有效的，我们可以登录用户
                # 我们将把用户送回主页。
                login(request, user)
                ret = {
                    'error': 0,
                    # 重定向
                    'url': reverse('qa_index')
                }
                # window.location.href = resp.url;
            else:
                # 使用了一个非活动帐户——没有登录
                ret = {
                    'error': 1,
                    'msg':'您的帐户被禁用'
                }
        else:
            # 提供了错误的登录细节。所以我们不能让用户登录.
            print("Invalid login details: {0}, {1}".format(username, password))
            ret = { 
                'error': 2,
                'msg':'提供的登录信息无效.'
            }
        return HttpResponse(json.dumps(ret), content_type='application/json')
    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        return render(request, 'login.html', {})


# Use the login_required() decorator to ensure only
# those logged in can access the view.
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/')
