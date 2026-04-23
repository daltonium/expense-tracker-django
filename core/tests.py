from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from .models import Workspace, Expense, Income, BudgetRule, Investment
import datetime
import decimal


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)

def make_workspace(user, name='Test Wallet', mode='personal'):
    return Workspace.objects.create(user=user, name=name, mode=mode)

def make_expense(workspace, title='Lunch', amount='250.00', category='food'):
    return Expense.objects.create(
        workspace=workspace, title=title,
        amount=decimal.Decimal(amount),
        category=category, date=datetime.date.today()
    )

def make_income(workspace, title='Salary', amount='50000.00', source='salary'):
    return Income.objects.create(
        workspace=workspace, title=title,
        amount=decimal.Decimal(amount),
        source=source, date=datetime.date.today()
    )

def make_investment(workspace, name='Nifty Fund', invested='10000', current='12000'):
    return Investment.objects.create(
        workspace=workspace, name=name,
        asset_type='mutual_fund',
        amount_invested=decimal.Decimal(invested),
        current_value=decimal.Decimal(current),
        date_invested=datetime.date.today(),
        status='active'
    )


# ─────────────────────────────────────────
# 1. MODEL TESTS
# ─────────────────────────────────────────
class WorkspaceModelTest(TestCase):

    def test_str(self):
        user = make_user()
        ws = make_workspace(user)
        self.assertEqual(str(ws), 'Test Wallet (personal)')

    def test_belongs_to_user(self):
        user = make_user()
        ws = make_workspace(user)
        self.assertEqual(ws.user, user)

    def test_company_mode(self):
        user = make_user()
        ws = make_workspace(user, mode='company')
        self.assertEqual(ws.mode, 'company')


class ExpenseModelTest(TestCase):

    def setUp(self):
        self.ws = make_workspace(make_user())

    def test_str(self):
        e = make_expense(self.ws, title='Groceries', amount='450.00')
        self.assertEqual(str(e), 'Groceries – ₹450.00')

    def test_note_optional(self):
        e = Expense.objects.create(
            workspace=self.ws, title='Bills',
            amount=decimal.Decimal('1200'), category='bills',
            date=datetime.date.today(), note=''
        )
        self.assertEqual(e.note, '')


class BudgetRuleModelTest(TestCase):

    def test_defaults(self):
        ws = make_workspace(make_user())
        rule = BudgetRule.objects.create(workspace=ws)
        self.assertEqual(rule.needs_percent, decimal.Decimal('50'))
        self.assertEqual(rule.wants_percent, decimal.Decimal('30'))
        self.assertEqual(rule.savings_percent, decimal.Decimal('20'))

    def test_one_rule_per_workspace(self):
        ws = make_workspace(make_user())
        BudgetRule.objects.create(workspace=ws)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            BudgetRule.objects.create(workspace=ws)


class InvestmentModelTest(TestCase):

    def setUp(self):
        self.ws = make_workspace(make_user())

    def test_returns_property(self):
        inv = make_investment(self.ws, invested='10000', current='12500')
        self.assertEqual(inv.returns, decimal.Decimal('2500'))

    def test_returns_percent(self):
        inv = make_investment(self.ws, invested='10000', current='12500')
        self.assertEqual(inv.returns_percent, decimal.Decimal('25'))

    def test_is_profitable_true(self):
        inv = make_investment(self.ws, invested='10000', current='12000')
        self.assertTrue(inv.is_profitable)

    def test_is_profitable_false(self):
        inv = make_investment(self.ws, invested='10000', current='8000')
        self.assertFalse(inv.is_profitable)

    def test_str(self):
        inv = make_investment(self.ws, name='Gold ETF', current='15000')
        self.assertEqual(str(inv), 'Gold ETF – ₹15000.00')


# ─────────────────────────────────────────
# 2. AUTH TESTS
# ─────────────────────────────────────────
class AuthTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
        self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass99!',
            'password2': 'complexpass99!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_redirects_to_select_mode(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass99!',
            'password2': 'complexpass99!',
        })
        self.assertRedirects(response, reverse('select_mode'))

    def test_login_valid_redirects_to_dashboard(self):
        make_user(username='loginuser', password='testpass123')
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_shows_error(self):
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

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertIn('/login/', response.url)

    def test_expense_list_requires_login(self):
        response = self.client.get(reverse('expense_list', args=[self.ws.id]))
        self.assertIn('/login/', response.url)

    def test_analytics_requires_login(self):
        response = self.client.get(reverse('analytics', args=[self.ws.id]))
        self.assertIn('/login/', response.url)

    def test_strategy_requires_login(self):
        response = self.client.get(reverse('strategy', args=[self.ws.id]))
        self.assertIn('/login/', response.url)

    def test_grow_requires_login(self):
        response = self.client.get(reverse('grow', args=[self.ws.id]))
        self.assertIn('/login/', response.url)

    def test_user_cannot_access_other_users_workspace(self):
        other_user = make_user(username='otheruser')
        other_ws = make_workspace(other_user, name='Other Wallet')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('expense_list', args=[other_ws.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_view_other_users_analytics(self):
        other_user = make_user(username='otheruser')
        other_ws = make_workspace(other_user)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('analytics', args=[other_ws.id]))
        self.assertEqual(response.status_code, 404)


# ─────────────────────────────────────────
# 4. DASHBOARD TESTS
# ─────────────────────────────────────────
class DashboardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_workspaces(self):
        response = self.client.get(reverse('dashboard'))
        self.assertIn(self.ws, response.context['workspaces'])

    def test_net_worth_calculation(self):
        make_income(self.ws, amount='50000')
        make_expense(self.ws, amount='20000')
        make_investment(self.ws, invested='10000', current='15000')
        response = self.client.get(reverse('dashboard'))
        # net worth = income(50000) - expenses(20000) + portfolio(15000) = 45000
        self.assertEqual(response.context['net_worth'], decimal.Decimal('45000'))


# ─────────────────────────────────────────
# 5. EXPENSE TESTS
# ─────────────────────────────────────────
class ExpenseTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_expense_list_loads(self):
        response = self.client.get(reverse('expense_list', args=[self.ws.id]))
        self.assertEqual(response.status_code, 200)

    def test_create_expense(self):
        self.client.post(reverse('expense_create', args=[self.ws.id]), {
            'title': 'Lunch', 'amount': '250.00',
            'category': 'food', 'date': '2026-04-23', 'note': '',
        })
        self.assertTrue(Expense.objects.filter(title='Lunch', workspace=self.ws).exists())

    def test_expense_amount_precision(self):
        self.client.post(reverse('expense_create', args=[self.ws.id]), {
            'title': 'Electricity', 'amount': '1850.50',
            'category': 'bills', 'date': '2026-04-23', 'note': '',
        })
        e = Expense.objects.get(title='Electricity')
        self.assertEqual(e.amount, decimal.Decimal('1850.50'))

    def test_invalid_expense_not_saved(self):
        self.client.post(reverse('expense_create', args=[self.ws.id]), {
            'title': '', 'amount': 'not_a_number',
            'category': 'food', 'date': '2026-04-23',
        })
        self.assertEqual(Expense.objects.count(), 0)

    def test_expense_list_shows_total(self):
        make_expense(self.ws, amount='1000')
        make_expense(self.ws, amount='500')
        response = self.client.get(reverse('expense_list', args=[self.ws.id]))
        self.assertEqual(response.context['total'], decimal.Decimal('1500'))


# ─────────────────────────────────────────
# 6. INCOME TESTS
# ─────────────────────────────────────────
class IncomeTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_create_income(self):
        self.client.post(reverse('income_create', args=[self.ws.id]), {
            'title': 'Salary', 'amount': '50000.00',
            'source': 'salary', 'date': '2026-04-23', 'note': '',
        })
        self.assertTrue(Income.objects.filter(title='Salary', workspace=self.ws).exists())

    def test_income_saved_to_correct_workspace(self):
        self.client.post(reverse('income_create', args=[self.ws.id]), {
            'title': 'Freelance', 'amount': '15000.00',
            'source': 'freelance', 'date': '2026-04-23', 'note': '',
        })
        income = Income.objects.get(title='Freelance')
        self.assertEqual(income.workspace, self.ws)


# ─────────────────────────────────────────
# 7. ANALYTICS TESTS
# ─────────────────────────────────────────
class AnalyticsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')
        make_expense(self.ws, title='Rent', amount='10000', category='bills')
        make_expense(self.ws, title='Food', amount='3000', category='food')

    def test_analytics_loads(self):
        response = self.client.get(reverse('analytics', args=[self.ws.id]))
        self.assertEqual(response.status_code, 200)

    def test_total_this_month(self):
        response = self.client.get(reverse('analytics', args=[self.ws.id]))
        self.assertEqual(response.context['total_this_month'], decimal.Decimal('13000'))

    def test_by_category_order(self):
        response = self.client.get(reverse('analytics', args=[self.ws.id]))
        categories = [row['category'] for row in response.context['by_category']]
        # bills(10000) should come before food(3000)
        self.assertEqual(categories[0], 'bills')


# ─────────────────────────────────────────
# 8. STRATEGY TESTS
# ─────────────────────────────────────────
class StrategyTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_strategy_loads(self):
        response = self.client.get(reverse('strategy', args=[self.ws.id]))
        self.assertEqual(response.status_code, 200)

    def test_budget_rule_created_on_first_visit(self):
        self.client.get(reverse('strategy', args=[self.ws.id]))
        self.assertTrue(BudgetRule.objects.filter(workspace=self.ws).exists())

    def test_invalid_percentages_rejected(self):
        self.client.get(reverse('strategy', args=[self.ws.id]))
        self.client.post(reverse('strategy', args=[self.ws.id]), {
            'needs_percent': '40',
            'wants_percent': '30',
            'savings_percent': '20',  # total = 90, not 100
        })
        rule = BudgetRule.objects.get(workspace=self.ws)
        self.assertEqual(rule.needs_percent, decimal.Decimal('50'))  # unchanged

    def test_valid_percentages_saved(self):
        self.client.get(reverse('strategy', args=[self.ws.id]))
        self.client.post(reverse('strategy', args=[self.ws.id]), {
            'needs_percent': '60',
            'wants_percent': '20',
            'savings_percent': '20',  # total = 100 ✓
        })
        rule = BudgetRule.objects.get(workspace=self.ws)
        self.assertEqual(rule.needs_percent, decimal.Decimal('60'))


# ─────────────────────────────────────────
# 9. GROW / INVESTMENT TESTS
# ─────────────────────────────────────────
class GrowTest(TestCase):

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
            'name': 'Nifty 50', 'asset_type': 'mutual_fund',
            'amount_invested': '50000', 'current_value': '58000',
            'date_invested': '2025-01-01', 'status': 'active', 'note': '',
        })
        self.assertTrue(Investment.objects.filter(name='Nifty 50').exists())

    def test_portfolio_totals_in_context(self):
        make_investment(self.ws, invested='10000', current='12000')
        make_investment(self.ws, invested='5000',  current='4500')
        response = self.client.get(reverse('grow', args=[self.ws.id]))
        self.assertEqual(response.context['total_invested'], decimal.Decimal('15000'))
        self.assertEqual(response.context['total_current'],  decimal.Decimal('16500'))
        self.assertEqual(response.context['total_returns'],  decimal.Decimal('1500'))

    def test_investment_update(self):
        inv = make_investment(self.ws, invested='10000', current='12000')
        self.client.post(
            reverse('investment_update', args=[self.ws.id, inv.id]), {
                'name': 'Updated Fund', 'asset_type': 'mutual_fund',
                'amount_invested': '10000', 'current_value': '14000',
                'date_invested': '2025-01-01', 'status': 'active', 'note': '',
            }
        )
        inv.refresh_from_db()
        self.assertEqual(inv.current_value, decimal.Decimal('14000'))


# ─────────────────────────────────────────
# 10. CHATBOT TESTS
# ─────────────────────────────────────────
class ChatbotTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ws = make_workspace(self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_chatbot_page_loads(self):
        response = self.client.get(reverse('chatbot', args=[self.ws.id]))
        self.assertEqual(response.status_code, 200)

    @patch('cohere.ClientV2')
    def test_chatbot_returns_ai_response(self, mock_cohere_class):
        mock_client = MagicMock()
        mock_cohere_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.message.content[0].text = 'You are saving well!'
        mock_client.chat.return_value = mock_response

        response = self.client.post(
            reverse('chatbot', args=[self.ws.id]),
            {'message': 'How am I doing?'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You are saving well!')

    def test_chatbot_empty_message_no_crash(self):
        response = self.client.post(
            reverse('chatbot', args=[self.ws.id]),
            {'message': ''}
        )
        self.assertEqual(response.status_code, 200)

    def test_chatbot_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('chatbot', args=[self.ws.id]))
        self.assertIn('/login/', response.url)