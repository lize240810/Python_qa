from annoying.fields import AutoOneToOneField
from django.conf import settings
from django.db import models
from django.db.models import F
# from django.utils.text import slugify
from uuslug import slugify
from django_markdown.models import MarkdownField
from hitcount.models import HitCountMixin
from taggit.managers import TaggableManager
from mdeditor.fields import MDTextField


class UserQAProfile(models.Model):
    """模型类为应用程序定义一个用户配置文件，直接链接
        到核心Django用户模型"""
    user = AutoOneToOneField(settings.AUTH_USER_MODEL, primary_key=True,
                             on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    # 我们希望包括的其他属性。
    website = models.URLField(blank=True)

    def modify_reputation(self, added_points):
        """核心功能是修改用户档案的信誉"""
        self.points = F('points') + added_points
        self.save()

    def __str__(self):  # pragma: no cover
        return self.user.username


class Question(models.Model, HitCountMixin):
    """模型类来包含论坛中的每个问题"""
    slug = models.SlugField(max_length=200)
    title = models.CharField(max_length=200, blank=False, verbose_name='标题')
    description = MarkdownField()
    pub_date = models.DateTimeField('出版日期', auto_now_add=True)
    tags = TaggableManager(verbose_name='标签',help_text='多个标签之间使用逗号分割')
    reward = models.IntegerField(default=0, verbose_name='奖金')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    closed = models.BooleanField(default=False)
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    class Meta:
        ordering = ['-pub_date']

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)
            try:
                points = settings.QA_SETTINGS['reputation']['CREATE_QUESTION']

            except KeyError:
                points = 0

            self.user.userqaprofile.modify_reputation(points)

        self.total_points = self.positive_votes - self.negative_votes
        super(Question, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Answer(models.Model):
    """模型类来包含论坛中的每个答案并链接它 正确的问题。."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = MarkdownField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    updated = models.DateTimeField('date updated', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = models.BooleanField(default=False)
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            points = settings.QA_SETTINGS['reputation']['CREATE_ANSWER']

        except KeyError:
            points = 0

        self.user.userqaprofile.modify_reputation(points)
        self.total_points = self.positive_votes - self.negative_votes
        super(Answer, self).save(*args, **kwargs)

    def __str__(self):  # pragma: no cover
        return self.answer_text

    class Meta:
        ordering = ['-answer', '-pub_date']


class VoteParent(models.Model):
    """抽象模型来定义每个投票的基本元素。"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AnswerVote(VoteParent):
    """模型类来包含答案的投票。"""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'answer'),)


class QuestionVote(VoteParent):
    """模型类来包含问题的投票。"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'question'),)


class BaseComment(models.Model):
    """抽象模型来定义每个注释的基本元素"""
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):  # pragma: no cover
        return self.comment_text


class AnswerComment(BaseComment):
    """模型类来包含答案的注释."""
    comment_text = MarkdownField()
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        try:
            points = settings.QA_SETTINGS['reputation']['CREATE_ANSWER_COMMENT']

        except KeyError:
            points = 0

        self.user.userqaprofile.modify_reputation(points)
        super(AnswerComment, self).save(*args, **kwargs)


class QuestionComment(BaseComment):
    """模型类来包含问题的注释."""
    comment_text = MarkdownField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        try:
            points = settings.QA_SETTINGS['reputation']['CREATE_QUESTION_COMMENT']

        except KeyError:
            points = 0

        self.user.userqaprofile.modify_reputation(points)
        super(QuestionComment, self).save(*args, **kwargs)


class ExampleModel(models.Model):
    name = models.CharField(max_length=10)
    content = MarkdownField()
