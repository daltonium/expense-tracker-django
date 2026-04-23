from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Workspace, Expense, Income, BudgetRule, Investment
import datetime
import decimal
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────
# HELPER: creates a user + workspace quickly
# ─────────────────────────────────────────
def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)

def make_workspace(user, name='Test Wallet', mode='personal'):
    return Workspace.objects.create(user=user, name=name, mode=mode)


# ─────────────────────────────────────────
# 1. MODEL TESTS
# ─────────────────────────────────────────
class WorkspaceModelTest(TestCase):

    def test_workspace_str(self):
        user = make_user()
        ws = make_workspace(user)
        self.assertEqual(str(ws), 'Test Wallet (personal)')

    def test_workspace_belongs_to_user(self):
        user = make_user()
        ws = make_workspace(user)
        self.assertEqual(ws.user, user)

    def test_workspace_mode_choices(self):
        user = make_user()
        ws = make_workspace(user, mode='company')
        self.assertEqual(ws.mode, 'company')


class ExpenseModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.ws = make_workspace(self.user)

    def test_expense_str(self):
        expense = Expense.objects.create(
            workspace=self.ws,
            title='Groceries',
            amount=decimal.Decimal('450.00'),
            category='grocery',
            date=datetime.date.today(),
        )
        self.assertEqual(str(expense), 'Groceries – ₹450.00')

    def test_expense_note_optional(self):
        # blank=True means note can be empty string
        expense = Expense.objects.create(
            workspace=self.ws,
            title='Bills',
            amount=decimal.Decimal('1200.00'),
            category='bills',
            date=datetime.date.today(),
            note='',
        )
        self.assertEqual(expense.note, '')

    def test_expense_belongs_to_workspace(self):
        expense = Expense.objects.create(
            workspace=self.ws,
            title='Food',
            amount=decimal.Decimal('200.00'),
            category='food',
            date=datetime.date.today(),
        )
        self.assertEqual(expense.workspace, self.ws)


class BudgetRuleModelTest(TestCase):

    def test_budget_rule_defaults(self):
        user = make_user()
        ws = make_workspace(user)
        rule = BudgetRule.objects.create(workspace=ws)
        self.assertEqual(rule.needs_percent, decimal.Decimal('50'))
        self.assertEqual(rule.wants_percent, decimal.Decimal('30'))
        self.assertEqual(rule.savings_percent, decimal.Decimal('20'))

    def test_one_budget_rule_per_workspace(self):
        user = make_user()
        ws = make_workspace(user)
        BudgetRule.objects.create(workspace=ws)
        # Creating a second one should raise an IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            BudgetRule.objects.create(workspace=ws)


# ─────────────────────────────────────────
# 2. AUTHENTICATION VIEW TESTS
# ─────────────────────────────────────────
class AuthViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass99!',
            'password2': 'complexpass99!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_redirects_to_home_after_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass99!',
            'password2': 'complexpass99!',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_with_valid_credentials(self):
        make_user(username='loginuser', password='testpass123')
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'nobody',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_logout_redirects_to_login(self):
        make_user()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


# ─────────────────────────────────────────
# 3. ACCESS CONTROL TESTS
# ─────────────────────────────────────────
class AccessControlTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)

    def test_dashboard_redirects_if_not_logged_in(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')

    def test_expense_list_redirects_if_not_logged_in(self):
        response = self.client.get(
            reverse('expense_list', args=[self.ws.id])
        )
        self.assertIn('/login/', response.url)

    def test_user_cannot_access_another_users_workspace(self):
        # Create a second user
        other_user = make_user(username='otheruser')
        other_ws = make_workspace(other_user, name='Other Wallet')

        # Login as first user and try to access second user's workspace
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('expense_list', args=[other_ws.id])
        )
        # Should get 404, not 200
        self.assertEqual(response.status_code, 404)


# ─────────────────────────────────────────
# 4. WORKSPACE TESTS
# ─────────────────────────────────────────
class WorkspaceViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')

    def test_select_mode_creates_workspace(self):
        self.client.post(reverse('select_mode'), {
            'mode': 'personal',
            'name': 'My Finances',
        })
        self.assertTrue(
            Workspace.objects.filter(user=self.user, name='My Finances').exists()
        )

    def test_invalid_mode_does_not_create_workspace(self):
        self.client.post(reverse('select_mode'), {
            'mode': 'invalid_mode',
            'name': 'Hacked Wallet',
        })
        self.assertFalse(
            Workspace.objects.filter(name='Hacked Wallet').exists()
        )


# ─────────────────────────────────────────
# 5. EXPENSE TESTS
# ─────────────────────────────────────────
class ExpenseViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_expense_list_loads(self):
        response = self.client.get(
            reverse('expense_list', args=[self.ws.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_create_expense(self):
        self.client.post(
            reverse('expense_create', args=[self.ws.id]), {
                'title': 'Lunch',
                'amount': '250.00',
                'category': 'food',
                'date': '2026-04-23',
                'note': '',
            }
        )
        self.assertTrue(
            Expense.objects.filter(title='Lunch', workspace=self.ws).exists()
        )

    def test_expense_amount_saved_correctly(self):
        self.client.post(
            reverse('expense_create', args=[self.ws.id]), {
                'title': 'Electricity',
                'amount': '1850.50',
                'category': 'bills',
                'date': '2026-04-23',
                'note': '',
            }
        )
        expense = Expense.objects.get(title='Electricity')
        self.assertEqual(expense.amount, decimal.Decimal('1850.50'))

    def test_invalid_expense_not_saved(self):
        self.client.post(
            reverse('expense_create', args=[self.ws.id]), {
                'title': '',           # title is required
                'amount': 'not_a_number',
                'category': 'food',
                'date': '2026-04-23',
            }
        )
        self.assertEqual(Expense.objects.count(), 0)


# ─────────────────────────────────────────
# 6. ANALYTICS TESTS
# ─────────────────────────────────────────
class AnalyticsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

        # Seed expenses
        Expense.objects.create(
            workspace=self.ws, title='Rent',
            amount=decimal.Decimal('10000'), category='bills',
            date=datetime.date.today()
        )
        Expense.objects.create(
            workspace=self.ws, title='Food',
            amount=decimal.Decimal('3000'), category='food',
            date=datetime.date.today()
        )

    def test_analytics_page_loads(self):
        response = self.client.get(
            reverse('analytics', args=[self.ws.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_total_this_month_is_correct(self):
        response = self.client.get(
            reverse('analytics', args=[self.ws.id])
        )
        self.assertEqual(
            response.context['total_this_month'],
            decimal.Decimal('13000')
        )


# ─────────────────────────────────────────
# 7. BUDGET RULE TESTS
# ─────────────────────────────────────────
class BudgetRuleTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_strategy_page_loads(self):
        response = self.client.get(
            reverse('strategy', args=[self.ws.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_budget_rule_created_on_first_visit(self):
        self.client.get(reverse('strategy', args=[self.ws.id]))
        self.assertTrue(
            BudgetRule.objects.filter(workspace=self.ws).exists()
        )

    def test_invalid_percentages_rejected(self):
        # 40+30+20 = 90, not 100 — should fail validation
        self.client.post(
            reverse('strategy', args=[self.ws.id]), {
                'needs_percent': '40',
                'wants_percent': '30',
                'savings_percent': '20',
            }
        )
        rule = BudgetRule.objects.get(workspace=self.ws)
        # Rule should still have defaults, not the invalid submission
        self.assertEqual(rule.needs_percent, decimal.Decimal('50'))

    def test_valid_percentages_saved(self):
        # First visit creates the rule
        self.client.get(reverse('strategy', args=[self.ws.id]))
        # Now update with valid percentages
        self.client.post(
            reverse('strategy', args=[self.ws.id]), {
                'needs_percent': '60',
                'wants_percent': '20',
                'savings_percent': '20',
            }
        )
        rule = BudgetRule.objects.get(workspace=self.ws)
        self.assertEqual(rule.needs_percent, decimal.Decimal('60'))
        
class ChatbotTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_chatbot_page_loads(self):
        response = self.client.get(
            reverse('chatbot', args=[self.ws.id])
        )
        self.assertEqual(response.status_code, 200)

    @patch('core.views.cohere.ClientV2')
    def test_chatbot_returns_response(self, mock_cohere_class):
        # Mock the Cohere API so tests don't make real network calls
        mock_client = MagicMock()
        mock_cohere_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.message.content[0].text = 'You are doing great!'
        mock_client.chat.return_value = mock_message

        response = self.client.post(
            reverse('chatbot', args=[self.ws.id]),
            {'message': 'How am I doing this month?'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You are doing great!')

    def test_chatbot_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse('chatbot', args=[self.ws.id])
        )
        self.assertIn('/login/', response.url)

class InvestmentTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_grow_page_loads(self):
        response = self.client.get(reverse('grow', args=[self.ws.id]))
        self.assertEqual(response.status_code, 200)

    def test_create_investment(self):
        self.client.post(reverse('investment_create', args=[self.ws.id]), {
            'name': 'Nifty 50 Index Fund',
            'asset_type': 'mutual_fund',
            'amount_invested': '50000.00',
            'current_value': '58000.00',
            'date_invested': '2025-01-01',
            'status': 'active',
            'note': '',
        })
        self.assertTrue(
            Investment.objects.filter(name='Nifty 50 Index Fund').exists()
        )

    def test_returns_property(self):
        inv = Investment.objects.create(
            workspace=self.ws,
            name='Test Stock',
            asset_type='stocks',
            amount_invested=decimal.Decimal('10000'),
            current_value=decimal.Decimal('12500'),
            date_invested=datetime.date.today(),
            status='active',
        )
        self.assertEqual(inv.returns, decimal.Decimal('2500'))
        self.assertEqual(inv.returns_percent, decimal.Decimal('25'))
        self.assertTrue(inv.is_profitable)