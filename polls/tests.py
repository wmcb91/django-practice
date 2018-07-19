import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice

def create_question(question_text, days=0, hours=0):
    """
    Create a question with the given `question_text` and published the
    given number of `days` and `hours` offset to now (negative for questions
    published in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days) + datetime.timedelta(hours=hours)
    return Question.objects.create(question_text=question_text, pub_date=time)

def create_choice(question, choice_text, votes=0):
    """
    Create a choice with the given `question (being an id)`, `choice_text` and 
    number of `votes`
    """
    q = Question.objects.get(pk=question.id)
    return q.choice_set.create(choice_text=choice_text, votes=votes)
    # return Choice.objects.create(question=question.id, choice_text=choice_text, votes=votes)

class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        q1 = create_question(question_text="Past question.", days=-30)
        create_choice(question=q1, choice_text='Question 1?', votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        q1 = create_question(question_text="Past question.", days=-30)
        q2 = create_question(question_text="Future question.", days=30)
        create_choice(question=q1, choice_text='Question 1?', votes=0)
        create_choice(question=q2, choice_text='Question 1?', votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        q1 = create_question(question_text="Past question 1.", days=-30)
        q2 = create_question(question_text="Past question 2.", days=-5)
        create_choice(question=q1, choice_text='Question 1?', votes=0)
        create_choice(question=q2, choice_text='Question 1?', votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )

    def test_questions_with_no_choices(self):
        """
        The questions index page does not display questions with 0 choices
        """
        # response = self.client.get(reverse('polls:index'))
        q1 = create_question(question_text="Past question 1.", days=-2)
        create_question(question_text="Past question 2.", days=-3)
        create_choice(question=q1, choice_text='Question 1?', votes=0)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 1.>']
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        create_choice(question=past_question, choice_text='Question 1?', votes=0)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
    
    def test_questions_with_no_choices(self):
        """
        The detail view of a question with no choices returns a 404 not found.
        """
        # response = self.client.get(reverse('polls:index'))
        no_choice_question = create_question(question_text="Past question 1.", days=-2)
        url = reverse('polls:detail', args=(no_choice_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        create_choice(question=past_question, choice_text='Question 1?', votes=0)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
    
    def test_questions_with_no_choices(self):
        """
        The detail view of a question with no choices returns a 404 not found.
        """
        # response = self.client.get(reverse('polls:index'))
        no_choice_question = create_question(question_text="Past question 1.", days=-2)
        url = reverse('polls:results', args=(no_choice_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_question__str__method_returns_expected(self):
        """
        Question.__str__() returns expect question_text
        """
        time = timezone.now()
        self.assertIs(
            Question(question_text='Test text', pub_date=time).__str__(),
            'Test text'
        )

        self.assertIsNot(
            Question(question_text='Test text', pub_date=time).__str__(),
            'Something else'
        )

class ChoiceModelTests(TestCase):

    def test_question__str__method_returns_expected(self):
        """
        Choice.__str__() returns expect choice_text
        """
        self.assertIs(
            Choice(choice_text='Test text').__str__(),
            'Test text'
        )

        self.assertIsNot(
            Choice(choice_text='Test text').__str__(),
            'Something else'
        )

    def test_question_votes_returns_expected(self):
        """
        Choice.votes returns expected
        """
        self.assertIs(Choice(choice_text='Test text').votes,0)
        self.assertIsNot(Choice(choice_text='Test text').votes,2)
        self.assertIs(Choice(choice_text='Test text', votes=3).votes,3)

