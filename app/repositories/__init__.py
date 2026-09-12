from app.repositories.base_repository import BaseRepository
from app.repositories.auth.user_repository import UserRepository
from app.repositories.catalog.catalog_repository import CategoryRepository, ProductRepository, ProductVariantRepository
from app.repositories.sales.sales_repository import SaleRepository, PaymentRepository
from app.repositories.inventory.inventory_repository import InventoryRepository, StockTransferRepository
from app.repositories.crm.crm_repository import CustomerRepository, SupplierRepository, LoyaltyRuleRepository, LoyaltyTransactionRepository
from app.repositories.procurement.procurement_repository import PurchaseRepository, GRNRepository

# Aliases for compatibility
CatalogRepository = ProductRepository
SalesRepository = SaleRepository
CRMRepository = CustomerRepository
