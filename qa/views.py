import operator
from functools import reduce

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, ListView, UpdateView, View
from django.http import JsonResponse, HttpResponse
from hitcount.views import HitCountDetailView
from qa.models import (Answer, AnswerComment, AnswerVote, Question,
                       QuestionComment, QuestionVote, UserQAProfile)
from taggit.models import Tag, TaggedItem

from .forms import QuestionForm
from .mixins import AuthorRequiredMixin, LoginRequired
from .utils import question_score

import json

try:
    qa_messages = 'django.contrib.messages' in settings.INSTALLED_APPS and\
        settings.QA_SETTINGS['qa_messages']

except AttributeError:  # pragma: no cover
    qa_messages = False

if qa_messages:
    from django.contrib import messages


"""亲爱的维护人员:

一旦您尝试“优化”这个例程，并意识到这是一个多么严重的错误，请增加以下计数器作为警告
下一个人:

total_hours_wasted_here = 2
"""


class AnswerQuestionView(LoginRequired, View):
    """
    查看是否选择一个答案作为该问题的满意答案，
    验证比创建que的用户
    只有问题才能使这些改变成为可能。.
    """
    model = Answer

    def post(self, request, answer_id):
        answer = get_object_or_404(self.model, pk=answer_id)
        if answer.question.user != request.user:
            raise ValidationError(
                "对不起，你不能结束这个问题")

        else:
            answer.question.answer_set.update(answer=False)
            answer.answer = True
            answer.save()

            try:
                points = settings.QA_SETTINGS['reputation']['ACCEPT_ANSWER']

            except KeyError:
                points = 0

            qa_user = UserQAProfile.objects.get(user=answer.user)
            qa_user.modify_reputation(points)

        next_url = request.POST.get('next', '')
        if next_url is not '':
            return redirect(next_url)

        else:
            return redirect(reverse('qa_index'))


class CloseQuestionView(LoginRequired, View):
    """视图
    将问题标记为closed，验证创建que问题的用户是唯一允许进行这些更改的用户.
    """
    model = Question

    def post(self, request, question_id):
        question = get_object_or_404(self.model, pk=question_id)
        if question.user != request.user:
            raise ValidationError(
                "对不起，你不能结束这个问题。")
        else:
            if not question.closed:
                question.closed = True

            else:
                raise ValidationError("对不起，这个问题已经结束了")

            question.save()

        next_url = request.POST.get('next', '')
        if next_url is not '':
            return redirect(next_url)

        else:
            return redirect(reverse('qa_index'))


class QuestionIndexView(ListView):
    """
        以呈现索引视图
    """
    model = Question
    paginate_by = 10
    context_object_name = 'questions'
    template_name = 'jQueryMoban/index.html'
    ordering = '-pub_date'

    def get_context_data(self, *args, **kwargs):
        context = super(QuestionIndexView, self).get_context_data(*args, **kwargs)
        noans = Question.objects.order_by('-pub_date').filter(
            answer__isnull=True).select_related('user')\
            .annotate(num_answers=Count('answer', distinct=True),
                      num_question_comments=Count('questioncomment',
                      distinct=True))
        context['totalcount'] = Question.objects.count()
        context['anscount'] = Answer.objects.count()
        paginator = Paginator(noans, 10)
        page = self.request.GET.get('noans_page')
        context['active_tab'] = self.request.GET.get('active_tab', 'latest')
        tabs = ['latest', 'unans', 'reward']
        context['active_tab'] = 'latest' if context['active_tab'] not in\
            tabs else context['active_tab']
        try:
            noans = paginator.page(page)

        except PageNotAnInteger:
            noans = paginator.page(1)

        except EmptyPage:  # pragma: no cover
            noans = paginator.page(paginator.num_pages)
        context['totalnoans'] = paginator.count
        context['noans'] = noans
        context['reward'] = Question.objects.order_by('-reward').filter(
            reward__gte=1)[:10]
        question_contenttype = ContentType.objects.get_for_model(Question)
        items = TaggedItem.objects.filter(content_type=question_contenttype)
        context['tags'] = Tag.objects.filter(
            taggit_taggeditem_items__in=items).order_by('-id').distinct()[:10]

        return context

    def get_queryset(self):
        queryset = super(QuestionIndexView, self).get_queryset()\
            .select_related('user')\
            .annotate(num_answers=Count('answer', distinct=True),
                      num_question_comments=Count('questioncomment',
                      distinct=True))
        return queryset


class QuestionsSearchView(QuestionIndexView):
    """
    显示从所筛选的QuestionIndexView继承的ListView页面
    搜索查询并按聚合的不同元素排序。
    """
    template_name = 'jQueryMoban/services.html'
    def get_queryset(self):
        result = super(QuestionsSearchView, self).get_queryset()
        query = self.request.GET.get('word', '')
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(operator.and_,
                       (Q(title__icontains=q) for q in query_list)) |
                reduce(operator.and_,
                       (Q(description__icontains=q) for q in query_list)))

        return result

    def get_context_data(self, *args, **kwargs):
        context = super(
            QuestionsSearchView, self).get_context_data(*args, **kwargs)
        context['totalcount'] = Question.objects.count
        context['anscount'] = Answer.objects.count
        context['noans'] = Question.objects.order_by('-pub_date').filter(
            answer__isnull=True)[:10]
        context['reward'] = Question.objects.order_by('-reward').filter(
            reward__gte=1)[:10]
        return context


class QuestionsByTagView(ListView):
    """
        查看是否在一个特定标记下调用所有clasiffied问题。
    """
    model = Question
    paginate_by = 10
    context_object_name = 'questions'
    
    template_name = 'jQueryMoban/services.html'

    def get_queryset(self, **kwargs):
        return Question.objects.filter(tags__slug=self.kwargs['tag'])

    def get_context_data(self, *args, **kwargs):
        context = super(
            QuestionsByTagView, self).get_context_data(*args, **kwargs)
        context['active_tab'] = self.request.GET.get('active_tab', 'latest')
        tabs = ['latest', 'unans', 'reward']
        context['active_tab'] = 'latest' if context['active_tab'] not in\
            tabs else context['active_tab']
        context['totalcount'] = Question.objects.count
        context['anscount'] = Answer.objects.count
        context['noans'] = Question.objects.order_by('-pub_date').filter(
            tags__name__contains=self.kwargs['tag'], answer__isnull=True)[:10]
        context['reward'] = Question.objects.order_by('-reward').filter(
            tags__name__contains=self.kwargs['tag'],
            reward__gte=1)[:10]
        context['totalnoans'] = len(context['noans'])
        return context


class CreateQuestionView(LoginRequired, CreateView):
    """
    视图来处理新问题的创建
    """
    template_name = 'jQueryMoban/contact.html'
    message = _('谢谢你！你的问题创建了。')
    form_class = QuestionForm

    def form_valid(self, form):
        """
        创建所需的关系
        """
        form.instance.user = self.request.user
        return super(CreateQuestionView, self).form_valid(form)

    def get_success_url(self):
        if qa_messages:
            messages.success(self.request, self.message)

        return reverse('qa_index')


class UpdateQuestionView(LoginRequired, AuthorRequiredMixin, UpdateView):
    """
    更新的问题
    """
    template_name = 'jQueryMoban/update_question.html'
    model = Question
    pk_url_kwarg = 'question_id'
    fields = ['title', 'description', 'tags']

    def get_success_url(self):
        question = self.get_object()
        return reverse('qa_detail', kwargs={'pk': question.pk})


class CreateAnswerView(LoginRequired, CreateView):
    """
    视图为给定问题创建新答案
    """
    
    template_name = 'jQueryMoban/create_answer.html'
    
    model = Answer
    fields = ['answer_text']
    message = _('谢谢你！你的答案已经贴出来了。')

    def form_valid(self, form):
        """
        Creates the required relationship between answer
        and user/question
        """
        form.instance.user = self.request.user
        form.instance.question_id = self.kwargs['question_id']
        return super(CreateAnswerView, self).form_valid(form)

    def get_success_url(self):
        if qa_messages:
            messages.success(self.request, self.message)

        return reverse('qa_detail', kwargs={'pk': self.kwargs['question_id']})


class UpdateAnswerView(LoginRequired, AuthorRequiredMixin, UpdateView):
    """
    Updates the question answer
    """
    # template_name = 'qa/update_answer.html'
    template_name = 'jQueryMoban/update_answer.html'
    model = Answer
    pk_url_kwarg = 'answer_id'
    fields = ['answer_text']

    def get_success_url(self):
        answer = self.get_object()
        return reverse('qa_detail', kwargs={'pk': answer.question.pk})


class CreateAnswerCommentView(LoginRequired, CreateView):
    """
    视图可为给定答案创建新评论
    """
    template_name = 'jQueryMoban/create_comment.html'
    model = AnswerComment
    fields = ['comment_text']
    message = _('谢谢你！你的评论已经发表了。')

    def form_valid(self, form):
        """
        在答案之间创建所需的关系 用户/发表评论
        """
        form.instance.user = self.request.user
        form.instance.answer_id = self.kwargs['answer_id']
        return super(CreateAnswerCommentView, self).form_valid(form)

    def get_success_url(self):
        if qa_messages:
            messages.success(self.request, self.message)

        question_pk = Answer.objects.get(
            id=self.kwargs['answer_id']).question.pk
        return reverse('qa_detail', kwargs={'pk': question_pk})


class CreateQuestionCommentView(LoginRequired, CreateView):
    """
    视图可为给定问题创建新评论
    """
    template_name = 'jQueryMoban/create_comment.html'
    model = QuestionComment
    fields = ['comment_text']
    message = ('谢谢你！你的评论已经发表了。')

    def form_valid(self, form):
        """
        创建问题之间所需的关系 和用户/发表评论
        """
        form.instance.user = self.request.user
        form.instance.question_id = self.kwargs['question_id']
        return super(CreateQuestionCommentView, self).form_valid(form)

    def get_success_url(self):
        if qa_messages:
            messages.success(self.request, self.message)

        return reverse('qa_detail', kwargs={'pk': self.kwargs['question_id']})


class UpdateQuestionCommentView(LoginRequired,
                                AuthorRequiredMixin, UpdateView):
    """
    更新评论问题
    """
    template_name = 'jQueryMoban/create_comment.html'
    model = QuestionComment
    pk_url_kwarg = 'comment_id'
    fields = ['comment_text']

    def get_success_url(self):
        question_comment = self.get_object()
        return reverse('qa_detail',
                       kwargs={'pk': question_comment.question.pk})


class UpdateAnswerCommentView(UpdateQuestionCommentView):
    """
    更新评论答案
    """
    model = AnswerComment
    def get_success_url(self):
        answer_comment = self.get_object()
        return reverse('qa_detail',
                       kwargs={'pk': answer_comment.answer.question.pk})


class QuestionDetailView(HitCountDetailView):
    """
    视图调用一个问题并呈现有关该问题的所有细节。
    """
    model = Question
    template_name = 'jQueryMoban/detail_question.html'
    
    context_object_name = 'question'
    slug_field = 'slug'
    try:
        count_hit = settings.QA_SETTINGS['count_hits']

    except KeyError:
        count_hit = True

    def get_context_data(self, **kwargs):
        answers = self.object.answer_set.all().order_by('pub_date')
        context = super(QuestionDetailView, self).get_context_data(**kwargs)
        context['last_comments'] = self.object.questioncomment_set.order_by(
            'pub_date')[:5]
        context['answers'] = list(answers.select_related(
            'user').select_related(
            'user__userqaprofile')
            .annotate(answercomment_count=Count('answercomment')))
        return context

    def get(self, request, **kwargs):
        my_object = self.get_object()
        slug = kwargs.get('slug', '')
        if slug != my_object.slug:
            kwargs['slug'] = my_object.slug
            return redirect(reverse('qa_detail', kwargs=kwargs))

        else:
            return super(QuestionDetailView, self).get(request, **kwargs)

    def get_object(self):
        question = super(QuestionDetailView, self).get_object()
        return question


class ParentVoteView(View):
    """
    为给定模型创建投票的基类(问题/答案)
    """
    model = None
    vote_model = None

    def get_vote_kwargs(self, user, vote_target):
        """
        这将获取用户和投票，并调整kwargs取决于使用的模型。
        """
        object_kwargs = {'user': user}
        if self.model == Question:
            target_key = 'question'

        elif self.model == Answer:
            target_key = 'answer'

        else:
            raise ValidationError('这不是一个有效的投票模型')

        object_kwargs[target_key] = vote_target
        return object_kwargs

    def post(self, request, object_id):
        vote_target = get_object_or_404(self.model, pk=object_id)
        if vote_target.user == request.user:
            raise ValidationError(
                '对不起，投票给你自己的答案是不可能的。')

        else:
            upvote = request.POST.get('upvote', None) is not None
            object_kwargs = self.get_vote_kwargs(request.user, vote_target)
            vote, created = self.vote_model.objects.get_or_create(
                defaults={'value': upvote},
                **object_kwargs)
            if created:
                vote_target.user.userqaprofile.points += 1 if upvote else -1
                if upvote:
                    vote_target.positive_votes += 1

                else:
                    vote_target.negative_votes += 1

            else:
                if vote.value == upvote:
                    vote.delete()
                    vote_target.user.userqaprofile.points += -1 if upvote else 1
                    if upvote:
                        vote_target.positive_votes -= 1

                    else:
                        vote_target.negative_votes -= 1

                else:
                    vote_target.user.userqaprofile.points += 2 if upvote else -2
                    vote.value = upvote
                    vote.save()
                    if upvote:
                        vote_target.positive_votes += 1
                        vote_target.negative_votes -= 1
                    else:
                        vote_target.negative_votes += 1
                        vote_target.positive_votes -= 1

            vote_target.user.userqaprofile.save()
            if self.model == Question:
                vote_target.reward = question_score(vote_target)

            if self.model == Answer:
                vote_target.question.reward = question_score(
                    vote_target.question)
                vote_target.question.save()

            vote_target.save()

        next_url = request.POST.get('next', '')
        if next_url is not '':
            return redirect(next_url)

        else:
            return redirect(reverse('qa_index'))


class AnswerVoteView(ParentVoteView):
    """
        投票表决答案
    """
    model = Answer
    vote_model = AnswerVote

class QuestionVoteView(ParentVoteView):
    """
        投票表决问题
    """
    model = Question
    vote_model = QuestionVote

    def ajax(self, request, *args, **kwargs):
        method = request.method.upper()
        req_data = getattr(request, method, {})
        next_url = req_data['next']
        upvote = req_data.get('upvote','')
        upvote = True if upvote == 'on' else False
        question_id = req_data['question_id']
        vote_target = get_object_or_404(self.model, pk=question_id)
        msg = None
        object_kwargs = self.get_vote_kwargs(request.user, vote_target)
        vote, created = self.vote_model.objects.get_or_create(
            defaults={'value': upvote}, **object_kwargs
        )
        if created:
            vote_target.user.userqaprofile.points += 1 if upvote else -1
            if upvote:
                vote_target.positive_votes += 1
            else:
                vote_target.negative_votes += 1
        else:
            if vote.value == upvote:
                vote.delete()
                vote_target.user.userqaprofile.points += -1 if upvote else 1
                if upvote:
                    vote_target.positive_votes -= 1

                else:
                    vote_target.negative_votes -= 1
            else:
                vote_target.user.userqaprofile.points += 2 if upvote else -2
                vote.value = upvote
                vote.save()
                if upvote:
                    vote_target.positive_votes += 1
                    vote_target.negative_votes -= 1
                else:
                    vote_target.negative_votes += 1
                    vote_target.positive_votes -= 1
        vote_target.user.userqaprofile.save()
        span = vote_target.positive_votes
        if self.model == Question:
            vote_target.reward = question_score(vote_target)
        if self.model == Answer:
            vote_target.question.reward = question_score(vote_target.question)
            vote_target.question.save()
        vote_target.save()
        ret = {
            'msg': span
        }
        return HttpResponse(json.dumps(ret), content_type='application/json')

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            if request.method.lower() in ['get', 'post']:
                handler = self.ajax
            else:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

def profile(request, user_id):
    user_ob = get_user_model().objects.get(id=user_id)
    user = UserQAProfile.objects.get(user=user_ob)
    context = {'user': user}
    return render(request, 'jQueryMoban/profile.html', context)


