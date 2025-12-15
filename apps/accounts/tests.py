from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class UserAuthenticationTestCase(TestCase):
    """Testes para autenticação de usuários."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com',
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Testa a criação de um novo usuário."""
        user = User.objects.create_user(
            username='newuser',
            password='newpass123',
            email='new@example.com'
        )
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('newpass123'))

    def test_user_login(self):
        """Testa o login de um usuário existente."""
        logged_in = self.client.login(
            username='testuser',
            password='testpass123'
        )
        self.assertTrue(logged_in)

    def test_user_login_wrong_password(self):
        """Testa login com senha incorreta."""
        logged_in = self.client.login(
            username='testuser',
            password='wrongpassword'
        )
        self.assertFalse(logged_in)

    def test_user_login_nonexistent_user(self):
        """Testa login com usuário que não existe."""
        logged_in = self.client.login(
            username='nonexistent',
            password='testpass123'
        )
        self.assertFalse(logged_in)

    def test_user_logout(self):
        """Testa o logout de um usuário."""
        self.client.login(username='testuser', password='testpass123')
        self.client.logout()
        # Após logout, a sessão deve estar vazia
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_update(self):
        """Testa a atualização de dados do usuário."""
        user = User.objects.get(username='testuser')
        user.email = 'newemail@example.com'
        user.save()
        
        updated_user = User.objects.get(username='testuser')
        self.assertEqual(updated_user.email, 'newemail@example.com')

    def test_user_delete(self):
        """Testa a deleção de um usuário."""
        user_id = self.user.id
        self.user.delete()
        
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)

    def test_user_password_change(self):
        """Testa a alteração de senha de um usuário."""
        user = User.objects.get(username='testuser')
        user.set_password('newpassword123')
        user.save()
        
        # Verifica se a nova senha funciona
        logged_in = self.client.login(
            username='testuser',
            password='newpassword123'
        )
        self.assertTrue(logged_in)

    def test_user_is_superuser(self):
        """Testa a criação de um superusuário."""
        superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@example.com'
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_duplicate_username(self):
        """Testa que não é permitido criar dois usuários com o mesmo username."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser',
                password='otherpass123'
            )
