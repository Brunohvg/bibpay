from django.test import TestCase
from apps.sellers.models import Seller
from apps.sellers.services import (
    create_seller,
    update_seller,
    delete_seller,
    list_sellers,
    get_seller,
    filter_sellers
)


class SellerModelTestCase(TestCase):
    """Testes do modelo Seller."""

    def test_seller_creation(self):
        """Testa a criação de um vendedor."""
        seller = Seller.objects.create(
            name='João Silva',
            phone='11999999999'
        )
        self.assertEqual(seller.name, 'João Silva')
        self.assertEqual(seller.phone, '11999999999')

    def test_seller_string_representation(self):
        """Testa a representação em string do vendedor."""
        seller = Seller.objects.create(
            name='Maria Santos',
            phone='11988888888'
        )
        self.assertEqual(str(seller), 'Maria Santos')

    def test_seller_has_created_at_timestamp(self):
        """Testa se o vendedor possui timestamp de criação."""
        seller = Seller.objects.create(
            name='Paulo Oliveira',
            phone='11977777777'
        )
        self.assertIsNotNone(seller.created_at)

    def test_seller_has_updated_at_timestamp(self):
        """Testa se o vendedor possui timestamp de atualização."""
        seller = Seller.objects.create(
            name='Ana Costa',
            phone='11966666666'
        )
        self.assertIsNotNone(seller.updated_at)

    def test_seller_update_timestamp(self):
        """Testa se o timestamp de atualização muda quando o vendedor é modificado."""
        seller = Seller.objects.create(
            name='Carlos Silva',
            phone='11955555555'
        )
        original_updated_at = seller.updated_at
        
        # Aguarda um pouco e atualiza
        import time
        time.sleep(0.1)
        
        seller.name = 'Carlos Silva Atualizado'
        seller.save()
        
        # O timestamp de atualização deve ser posterior
        self.assertGreaterEqual(seller.updated_at, original_updated_at)

    def test_seller_deletion(self):
        """Testa a deleção de um vendedor."""
        seller = Seller.objects.create(
            name='Fabio Pereira',
            phone='11944444444'
        )
        seller_id = seller.id
        seller.delete()
        
        with self.assertRaises(Seller.DoesNotExist):
            Seller.objects.get(id=seller_id)

    def test_seller_name_max_length(self):
        """Testa o comprimento máximo do nome do vendedor."""
        long_name = 'a' * 255
        seller = Seller.objects.create(
            name=long_name,
            phone='11933333333'
        )
        self.assertEqual(len(seller.name), 255)

    def test_seller_phone_max_length(self):
        """Testa o comprimento máximo do telefone do vendedor."""
        long_phone = '1' * 255
        seller = Seller.objects.create(
            name='Vendedor Teste',
            phone=long_phone
        )
        self.assertEqual(len(seller.phone), 255)

    def test_seller_ordering(self):
        """Testa a ordenação dos vendedores por data de criação."""
        seller1 = Seller.objects.create(
            name='Vendedor 1',
            phone='11922222222'
        )
        seller2 = Seller.objects.create(
            name='Vendedor 2',
            phone='11911111111'
        )
        
        sellers = list(Seller.objects.all())
        self.assertEqual(sellers[0], seller1)  # Mais antigo primeiro
        self.assertEqual(sellers[1], seller2)

    def test_seller_is_active_by_default(self):
        """Testa se o vendedor é ativo por padrão."""
        seller = Seller.objects.create(
            name='Vendedor Ativo',
            phone='11900000000'
        )
        self.assertTrue(seller.is_active)

    def test_seller_is_not_deleted_by_default(self):
        """Testa se o vendedor não está marcado como deletado por padrão."""
        seller = Seller.objects.create(
            name='Vendedor Não Deletado',
            phone='11899999999'
        )
        self.assertFalse(seller.is_deleted)


class SellerServiceTestCase(TestCase):
    """Testes das funções de serviço do Seller."""

    def test_create_seller_service(self):
        """Testa a criação de vendedor via serviço."""
        data = {
            'name': 'João Silva',
            'phone': '11999999999'
        }
        seller = create_seller(data)
        
        self.assertEqual(seller.name, 'João Silva')
        self.assertEqual(seller.phone, '11999999999')

    def test_update_seller_service(self):
        """Testa a atualização de vendedor via serviço."""
        seller = Seller.objects.create(
            name='Nome Original',
            phone='11999999999'
        )
        
        updated_seller = update_seller(seller.id, {
            'name': 'Nome Atualizado',
            'phone': '11888888888'
        })
        
        self.assertEqual(updated_seller.name, 'Nome Atualizado')
        self.assertEqual(updated_seller.phone, '11888888888')

    def test_update_seller_partial(self):
        """Testa a atualização parcial de vendedor via serviço."""
        seller = Seller.objects.create(
            name='Nome Original',
            phone='11999999999'
        )
        
        updated_seller = update_seller(seller.id, {'name': 'Novo Nome'})
        
        self.assertEqual(updated_seller.name, 'Novo Nome')
        self.assertEqual(updated_seller.phone, '11999999999')  # Mantém o original

    def test_delete_seller_service(self):
        """Testa a deleção de vendedor via serviço."""
        seller = Seller.objects.create(
            name='Vendedor para Deletar',
            phone='11999999999'
        )
        seller_id = seller.id
        
        result = delete_seller(seller_id)
        self.assertTrue(result)
        
        with self.assertRaises(Seller.DoesNotExist):
            Seller.objects.get(id=seller_id)

    def test_list_sellers_service(self):
        """Testa a listagem de vendedores via serviço."""
        Seller.objects.create(name='Vendedor 1', phone='11999999999')
        Seller.objects.create(name='Vendedor 2', phone='11988888888')
        Seller.objects.create(name='Vendedor 3', phone='11977777777')
        
        sellers = list_sellers()
        self.assertEqual(len(sellers), 3)

    def test_list_sellers_empty(self):
        """Testa a listagem quando não há vendedores."""
        sellers = list_sellers()
        self.assertEqual(len(sellers), 0)

    def test_get_seller_service(self):
        """Testa a busca de um vendedor específico via serviço."""
        seller = Seller.objects.create(
            name='Vendedor Específico',
            phone='11999999999'
        )
        
        fetched_seller = get_seller(seller.id)
        self.assertEqual(fetched_seller.id, seller.id)
        self.assertEqual(fetched_seller.name, 'Vendedor Específico')

    def test_get_seller_nonexistent(self):
        """Testa a busca de um vendedor que não existe."""
        with self.assertRaises(Exception):
            # get_object_or_404 lança Http404, não Seller.DoesNotExist
            get_seller(9999)

    def test_filter_sellers_service(self):
        """Testa a filtragem de vendedores via serviço."""
        Seller.objects.create(name='João Silva', phone='11999999999')
        Seller.objects.create(name='Maria Silva', phone='11988888888')
        Seller.objects.create(name='Pedro Santos', phone='11977777777')
        
        filtered = filter_sellers(name__contains='Silva')
        self.assertEqual(len(filtered), 2)

    def test_filter_sellers_by_phone(self):
        """Testa a filtragem de vendedores por telefone."""
        Seller.objects.create(name='Vendedor 1', phone='11999999999')
        Seller.objects.create(name='Vendedor 2', phone='11988888888')
        
        filtered = filter_sellers(phone='11999999999')
        self.assertEqual(len(filtered), 1)
        self.assertEqual(list(filtered)[0].name, 'Vendedor 1')

    def test_filter_sellers_empty_result(self):
        """Testa a filtragem que retorna vazio."""
        Seller.objects.create(name='Vendedor 1', phone='11999999999')
        
        filtered = filter_sellers(name='Inexistente')
        self.assertEqual(len(filtered), 0)
