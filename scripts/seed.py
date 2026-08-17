"""
Idempotent database seeding script for WareFlow wholesale distribution platform.

Seeds:
- 2 Base Units of Measure (piece, case) with Product UOM Conversions
- 5 Product Categories
- ~40 Wholesale Products across categories
- 2 Warehouses
- 5 Suppliers with FSSAI & GST details
- 8 Retailers with mixed pricing tiers and credit limits
- 5 Default RBAC Roles & Granular Permission Matrix
- Stock Batches (including at least 3 low-stock products below reorder point)
- Business Settings profile

Run directly with:
    python scripts/seed.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure apps/api is in Python path
REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Load environment variables from apps/api/.env if present
from dotenv import load_dotenv

env_path = API_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.models import (
    BusinessSettings,
    Category,
    Permission,
    Product,
    ProductUOMConversion,
    Retailer,
    Role,
    RolePermission,
    StockBatch,
    Supplier,
    UnitOfMeasure,
    Warehouse,
)


def get_or_create_uom(db: Session, name: str, abbreviation: str) -> UnitOfMeasure:
    """Get existing or create a new Unit of Measure by abbreviation."""
    uom = db.execute(
        select(UnitOfMeasure).where(UnitOfMeasure.abbreviation == abbreviation)
    ).scalar_one_or_none()
    if not uom:
        uom = UnitOfMeasure(name=name, abbreviation=abbreviation)
        db.add(uom)
        db.flush()
    return uom


def get_or_create_category(db: Session, name: str, parent_id: str | None = None) -> Category:
    """Get existing or create a new Category by name."""
    cat = db.execute(select(Category).where(Category.name == name)).scalar_one_or_none()
    if not cat:
        cat = Category(name=name, parent_id=parent_id)
        db.add(cat)
        db.flush()
    return cat


def get_or_create_warehouse(db: Session, name: str, location: str) -> Warehouse:
    """Get existing or create a new Warehouse by name."""
    wh = db.execute(select(Warehouse).where(Warehouse.name == name)).scalar_one_or_none()
    if not wh:
        wh = Warehouse(name=name, location=location, is_active=True)
        db.add(wh)
        db.flush()
    else:
        wh.location = location
        db.flush()
    return wh


def upsert_supplier(
    db: Session,
    name: str,
    contact_person: str,
    phone: str,
    email: str,
    address: str,
    gstin: str,
    fssai: str,
    expiry: date,
) -> Supplier:
    """Upsert supplier by name."""
    sup = db.execute(select(Supplier).where(Supplier.name == name)).scalar_one_or_none()
    if not sup:
        sup = Supplier(
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            gstin=gstin,
            fssai_license_no=fssai,
            fssai_expiry_date=expiry,
            is_active=True,
        )
        db.add(sup)
        db.flush()
    else:
        sup.contact_person = contact_person
        sup.phone = phone
        sup.email = email
        sup.address = address
        sup.gstin = gstin
        sup.fssai_license_no = fssai
        sup.fssai_expiry_date = expiry
        db.flush()
    return sup


def upsert_retailer(
    db: Session,
    name: str,
    contact: str,
    phone: str,
    email: str,
    address: str,
    gstin: str,
    tier: str,
    limit: float,
    balance: float,
) -> Retailer:
    """Upsert retailer by name."""
    ret = db.execute(select(Retailer).where(Retailer.name == name)).scalar_one_or_none()
    if not ret:
        ret = Retailer(
            name=name,
            contact_person=contact,
            phone=phone,
            email=email,
            address=address,
            gstin=gstin,
            pricing_tier=tier,
            credit_limit=limit,
            credit_balance=balance,
            is_active=True,
        )
        db.add(ret)
        db.flush()
    else:
        ret.contact_person = contact
        ret.phone = phone
        ret.email = email
        ret.address = address
        ret.gstin = gstin
        ret.pricing_tier = tier
        ret.credit_limit = limit
        ret.credit_balance = balance
        db.flush()
    return ret


def upsert_product(
    db: Session,
    sku: str,
    name: str,
    desc: str,
    hsn: str,
    barcode: str,
    cat_id: str,
    uom_id: str,
    cost: float,
    wholesale: float,
    reorder_point: float,
    reorder_qty: float,
) -> Product:
    """Upsert product by unique SKU."""
    prod = db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
    if not prod:
        prod = Product(
            sku=sku,
            name=name,
            description=desc,
            hsn_code=hsn,
            barcode=barcode,
            category_id=cat_id,
            base_uom_id=uom_id,
            unit="pcs",
            cost_price=cost,
            wholesale_price=wholesale,
            reorder_point=reorder_point,
            reorder_qty=reorder_qty,
            is_active=True,
        )
        db.add(prod)
        db.flush()
    else:
        prod.name = name
        prod.description = desc
        prod.hsn_code = hsn
        prod.barcode = barcode
        prod.category_id = cat_id
        prod.base_uom_id = uom_id
        prod.cost_price = cost
        prod.wholesale_price = wholesale
        prod.reorder_point = reorder_point
        prod.reorder_qty = reorder_qty
        db.flush()
    return prod


def get_or_create_permission(db: Session, code: str, desc: str) -> Permission:
    """Get existing or create permission by code."""
    perm = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
    if not perm:
        perm = Permission(code=code, description=desc)
        db.add(perm)
        db.flush()
    return perm


def get_or_create_role(db: Session, name: str, desc: str) -> Role:
    """Get existing or create role by name."""
    role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if not role:
        role = Role(name=name, description=desc)
        db.add(role)
        db.flush()
    return role


def sync_role_permission(db: Session, role_id: str, perm_id: str):
    """Ensure mapping between role and permission exists."""
    mapping = db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == perm_id,
        )
    ).scalar_one_or_none()
    if not mapping:
        mapping = RolePermission(role_id=role_id, permission_id=perm_id)
        db.add(mapping)
        db.flush()


def upsert_stock_batch(
    db: Session,
    prod_id: str,
    wh_id: str,
    batch_no: str,
    qty: float,
    exp_date: date | None = None,
) -> StockBatch:
    """Upsert stock batch by batch_no, prod_id, wh_id."""
    batch = db.execute(
        select(StockBatch).where(
            StockBatch.product_id == prod_id,
            StockBatch.warehouse_id == wh_id,
            StockBatch.batch_no == batch_no,
        )
    ).scalar_one_or_none()
    if not batch:
        batch = StockBatch(
            product_id=prod_id,
            warehouse_id=wh_id,
            batch_no=batch_no,
            quantity=qty,
            expiry_date=exp_date,
        )
        db.add(batch)
        db.flush()
    else:
        batch.quantity = qty
        batch.expiry_date = exp_date
        db.flush()
    return batch


def seed_database():
    """Main database seeding orchestration function."""
    print("🌱 Connecting to database for seeding...")
    engine = get_engine()
    with Session(engine) as db:
        # 1. Units of Measure
        print("-> Seeding Units of Measure...")
        uom_pcs = get_or_create_uom(db, "Piece", "pcs")
        uom_case = get_or_create_uom(db, "Case (24 pcs)", "case")
        uom_kg = get_or_create_uom(db, "Kilogram", "kg")
        uom_box = get_or_create_uom(db, "Box (10 pcs)", "box")

        # 2. Warehouses
        print("-> Seeding Warehouses...")
        wh_bhiwandi = get_or_create_warehouse(
            db,
            "Bhiwandi Central Hub",
            "Building A-4, Indian Corporation Logistics Park, Bhiwandi, MH 421302",
        )
        wh_vashi = get_or_create_warehouse(
            db, "Navi Mumbai APMC Terminal", "Sector 19, APMC Market, Vashi, Navi Mumbai, MH 400703"
        )

        # 3. Suppliers (with FSSAI + GSTIN)
        print("-> Seeding Suppliers...")
        sup_hul = upsert_supplier(
            db,
            "Hindustan Unilever Limited",
            "Rajesh Khandelwal",
            "+912239830000",
            "distributor.sales@hul.com",
            "Unilever House, B. D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
            "27AAACH2702H1Z1",
            "10012022000245",
            date(2028, 6, 30),
        )
        sup_itc = upsert_supplier(
            db,
            "ITC Limited — Foods Division",
            "Vikram Sengupta",
            "+913322889371",
            "trade.orders@itc.in",
            "Virginia House, 37 J. L. Nehru Road, Kolkata 700071",
            "19AAACI0076R1ZP",
            "10012031000085",
            date(2027, 12, 31),
        )
        sup_tata = upsert_supplier(
            db,
            "Tata Consumer Products Ltd",
            "Sunil Deshmukh",
            "+912266658282",
            "wholesale@tataconsumer.com",
            "11/13 Botawala Building, Horniman Circle, Fort, Mumbai 400001",
            "27AAACT0587F1Z3",
            "10014022002759",
            date(2029, 3, 31),
        )
        sup_nestle = upsert_supplier(
            db,
            "Nestle India Limited",
            "Pooja Batra",
            "+911242389300",
            "supplychain@in.nestle.com",
            "Nestle House, Jacaranda Marg, DLF City Phase II, Gurugram 122002",
            "06AAACN0149C1ZV",
            "10012011000168",
            date(2028, 9, 30),
        )
        sup_britannia = upsert_supplier(
            db,
            "Britannia Industries Limited",
            "Alok Verma",
            "+918039400000",
            "dist.mumbai@britindia.com",
            "5/1A Hungerford Street, Kolkata 700017",
            "19AAACB0504M1ZT",
            "10015043001129",
            date(2027, 8, 15),
        )

        # 4. Retailers (Mixed Tiers & Credit Limits)
        print("-> Seeding Retailers...")
        upsert_retailer(
            db,
            "Aapla Supermarket & Mart",
            "Mahesh Gaikwad",
            "+919820112233",
            "accounts@aaplamart.com",
            "Shop 1-4, Sai Heritage, Sector 20, Kharghar, Navi Mumbai 410210",
            "27AABCU9603R1ZM",
            "wholesale_gold",
            250000.00,
            48500.00,
        )
        upsert_retailer(
            db,
            "Shree Ganesh Kirana Stores",
            "Ganesh Patil",
            "+919819223344",
            "ganesh.patil.kirana@gmail.com",
            "Station Road, Near Railway Phatak, Thane West 400601",
            "27AAEFG4567P1Z5",
            "standard",
            50000.00,
            12400.00,
        )
        upsert_retailer(
            db,
            "Metro Cash & Carry Partner Hub",
            "Sandeep Kulkarni",
            "+919892334455",
            "procurement@metrohub.in",
            "Plot 88, MIDC Industrial Area, Turbhe, Navi Mumbai 400705",
            "27AACCM1234K1Z9",
            "vip",
            500000.00,
            185000.00,
        )
        upsert_retailer(
            db,
            "Jai Hind Provision Store",
            "Ramesh Lalvani",
            "+919820445566",
            "jaihindprovision@rediffmail.com",
            "Market Yard, Ulhasnagar 421002",
            "27AABPJ3322L1ZX",
            "wholesale_silver",
            100000.00,
            0.00,
        )
        upsert_retailer(
            db,
            "Royal Bakers & Mart",
            "Imran Merchant",
            "+919870556677",
            "royalbakersmart@gmail.com",
            "Mohammed Ali Road, Bhendi Bazaar, Mumbai 400003",
            "27AAGCR8899N1Z2",
            "standard",
            30000.00,
            8200.00,
        )
        upsert_retailer(
            db,
            "Sahyadri Mini Mart",
            "Dattatray Shinde",
            "+919821667788",
            "sahyadri.mart@yahoo.com",
            "Panchpakhadi, Near Nitin Co., Thane West 400602",
            "27AAFFS6655H1ZP",
            "wholesale_silver",
            75000.00,
            24500.00,
        )
        upsert_retailer(
            db,
            "Laxmi Narayan Super Market",
            "Narendra Gupta",
            "+919833778899",
            "laxmi.supermarket@outlook.com",
            "LBS Marg, Ghatkopar West, Mumbai 400086",
            "27AABBL7788Q1ZR",
            "wholesale_gold",
            200000.00,
            0.00,
        )
        upsert_retailer(
            db,
            "Kalyan Wholesale Traders",
            "Pravin Oswal",
            "+919822889900",
            "oswal.kalyan@gmail.com",
            "Bazar Peth, Near Subhash Chowk, Kalyan 421301",
            "27AAAKO9900P1ZT",
            "vip",
            400000.00,
            92000.00,
        )

        # 5. Product Categories
        print("-> Seeding Categories...")
        cat_staples = get_or_create_category(db, "Staples & Grains")
        cat_bev = get_or_create_category(db, "Beverages & Tea")
        cat_snacks = get_or_create_category(db, "Snacks & Biscuits")
        cat_personal = get_or_create_category(db, "Personal Care & Hygiene")
        cat_packaged = get_or_create_category(db, "Packaged Foods & Sauces")

        # 6. ~40 Products across Categories
        print("-> Seeding Products (~40 SKUs)...")
        products_data = [
            # Category: Staples & Grains
            (
                "SKU-RICE-BAS-5KG",
                "Daawat Rozana Basmati Rice 5kg",
                "Premium long grain everyday basmati rice",
                "100630",
                "8901537001011",
                cat_staples.id,
                uom_pcs.id,
                320.00,
                380.00,
                50.0,
                100.0,
            ),
            (
                "SKU-RICE-KOL-10KG",
                "Kolam Steam Rice Premium 10kg",
                "Sortex cleaned aged steam kolam rice",
                "100630",
                "8901537001028",
                cat_staples.id,
                uom_pcs.id,
                520.00,
                610.00,
                40.0,
                80.0,
            ),
            (
                "SKU-ATTA-AAS-10KG",
                "Aashirvaad Superior MP Atta 10kg",
                "100% whole wheat 0% maida chakki atta",
                "110100",
                "8901725181123",
                cat_staples.id,
                uom_pcs.id,
                390.00,
                445.00,
                60.0,
                120.0,
            ),
            (
                "SKU-ATTA-AAS-5KG",
                "Aashirvaad Whole Wheat Atta 5kg",
                "100% whole wheat chakki atta 5kg pouch",
                "110100",
                "8901725181130",
                cat_staples.id,
                uom_pcs.id,
                205.00,
                235.00,
                80.0,
                150.0,
            ),
            (
                "SKU-OIL-FORT-1L",
                "Fortune Sunlite Refined Sunflower Oil 1L",
                "Refined sunflower cooking oil pouch",
                "151219",
                "8906007281014",
                cat_staples.id,
                uom_pcs.id,
                105.00,
                122.00,
                100.0,
                200.0,
            ),
            (
                "SKU-OIL-FORT-5L",
                "Fortune Refined Sunflower Oil Jar 5L",
                "Refined cooking oil 5L heavy-duty jar",
                "151219",
                "8906007281052",
                cat_staples.id,
                uom_pcs.id,
                540.00,
                625.00,
                30.0,
                60.0,
            ),
            (
                "SKU-PULSE-TOOR-1KG",
                "Tata Sampann Unpolished Toor Dal 1kg",
                "Unpolished protein-rich toor/arhar dal",
                "071360",
                "8904043901112",
                cat_staples.id,
                uom_pcs.id,
                145.00,
                172.00,
                40.0,
                80.0,
            ),
            (
                "SKU-PULSE-MOONG-1KG",
                "Tata Sampann Unpolished Moong Dal 1kg",
                "Yellow split unpolished moong dal",
                "071331",
                "8904043901129",
                cat_staples.id,
                uom_pcs.id,
                125.00,
                148.00,
                35.0,
                70.0,
            ),
            (
                "SKU-SUGAR-MADH-5KG",
                "Madhur Pure & Hygienic Sugar 5kg",
                "Sulphur-free refined crystalline sugar",
                "170199",
                "8906014640057",
                cat_staples.id,
                uom_pcs.id,
                220.00,
                255.00,
                50.0,
                100.0,
            ),
            (
                "SKU-SALT-TATA-1KG",
                "Tata Salt Vacuum Evaporated 1kg",
                "Iodized vacuum evaporated refined salt",
                "250100",
                "8904043900016",
                cat_staples.id,
                uom_pcs.id,
                21.00,
                26.00,
                150.0,
                300.0,
            ),
            # Category: Beverages & Tea
            (
                "SKU-TEA-TATAG-1KG",
                "Tata Tea Gold Leaf Tea 1kg",
                "Gently rolled fragrant long leaves blend",
                "090240",
                "8901052002105",
                cat_bev.id,
                uom_pcs.id,
                460.00,
                540.00,
                40.0,
                80.0,
            ),
            (
                "SKU-TEA-TATAP-500G",
                "Tata Tea Premium Desh Ki Chai 500g",
                "Finest grain CTC rich blend",
                "090240",
                "8901052002051",
                cat_bev.id,
                uom_pcs.id,
                195.00,
                230.00,
                60.0,
                120.0,
            ),
            (
                "SKU-TEA-REDL-500G",
                "Brooke Bond Red Label Tea 500g",
                "Rich taste with healthy flavonoids",
                "090240",
                "8901030381017",
                cat_bev.id,
                uom_pcs.id,
                190.00,
                225.00,
                50.0,
                100.0,
            ),
            (
                "SKU-TEA-TAJ-500G",
                "Brooke Bond Taj Mahal Tea 500g",
                "Exquisite gourmet aroma tea",
                "090240",
                "8901030382014",
                cat_bev.id,
                uom_pcs.id,
                280.00,
                335.00,
                30.0,
                60.0,
            ),
            (
                "SKU-COF-NESC-200G",
                "Nescafe Classic Instant Coffee Jar 200g",
                "100% pure instant coffee powder",
                "210111",
                "8901058852315",
                cat_bev.id,
                uom_pcs.id,
                480.00,
                575.00,
                25.0,
                50.0,
            ),
            (
                "SKU-COF-NESC-50G",
                "Nescafe Classic Coffee Jar 50g",
                "Pure instant coffee glass jar 50g",
                "210111",
                "8901058852308",
                cat_bev.id,
                uom_pcs.id,
                140.00,
                168.00,
                45.0,
                90.0,
            ),
            (
                "SKU-COF-BRU-200G",
                "Bru Instant Coffee Chicory Mix 200g",
                "Roasted coffee chicory blend refill pouch",
                "210112",
                "8901030401012",
                cat_bev.id,
                uom_pcs.id,
                310.00,
                370.00,
                35.0,
                70.0,
            ),
            (
                "SKU-DRK-BOURN-1KG",
                "Cadbury Bournvita Health Drink Refill 1kg",
                "Nutrition chocolate health drink mix",
                "180690",
                "8901233024019",
                cat_bev.id,
                uom_pcs.id,
                360.00,
                425.00,
                30.0,
                60.0,
            ),
            # Category: Snacks & Biscuits
            (
                "SKU-BIS-PARLEG-800G",
                "Parle-G Glucose Biscuits Mega Pack 800g",
                "Original glucose biscuit family pack",
                "190531",
                "8901719101014",
                cat_snacks.id,
                uom_pcs.id,
                65.00,
                78.00,
                100.0,
                200.0,
            ),
            (
                "SKU-BIS-BRIT-MARIE-1KG",
                "Britannia Marie Gold Biscuits 1kg",
                "Crispy light tea-time marie biscuits",
                "190531",
                "8901063011011",
                cat_snacks.id,
                uom_pcs.id,
                110.00,
                132.00,
                60.0,
                120.0,
            ),
            (
                "SKU-BIS-BRIT-GOOD-600G",
                "Britannia Good Day Butter Cookies 600g",
                "Rich butter cookie family value pack",
                "190531",
                "8901063022017",
                cat_snacks.id,
                uom_pcs.id,
                105.00,
                126.00,
                70.0,
                140.0,
            ),
            (
                "SKU-BIS-BRIT-BOURB-400G",
                "Britannia Bourbon Chocolate Cream 400g",
                "Thick chocolate cream sandwich biscuits",
                "190531",
                "8901063033013",
                cat_snacks.id,
                uom_pcs.id,
                75.00,
                92.00,
                40.0,
                80.0,
            ),
            (
                "SKU-SNK-HALD-BHUJ-1KG",
                "Haldiram's Nagpur Bhujia Sev 1kg",
                "Spicy crispy moth bean & besan bhujia",
                "210690",
                "8904063201018",
                cat_snacks.id,
                uom_pcs.id,
                210.00,
                255.00,
                40.0,
                80.0,
            ),
            (
                "SKU-SNK-HALD-KHAT-1KG",
                "Haldiram's Khatta Meetha Mixture 1kg",
                "Sweet and sour crispy namkeen mix",
                "210690",
                "8904063201025",
                cat_snacks.id,
                uom_pcs.id,
                195.00,
                238.00,
                35.0,
                70.0,
            ),
            (
                "SKU-SNK-LAY-CLAS-50G",
                "Lay's Classic Salted Potato Chips 50g",
                "Crispy salted potato chips pack",
                "200520",
                "8901491101016",
                cat_snacks.id,
                uom_pcs.id,
                16.50,
                20.00,
                120.0,
                240.0,
            ),
            (
                "SKU-SNK-KURK-MAS-75G",
                "Kurkure Masala Munch Crisps 75g",
                "Spicy crunchy corn puffs snack",
                "200520",
                "8901491102013",
                cat_snacks.id,
                uom_pcs.id,
                16.50,
                20.00,
                120.0,
                240.0,
            ),
            # Category: Personal Care & Hygiene
            (
                "SKU-SOAP-DOVE-3X100G",
                "Dove Beauty Cream Bathing Bar 3x100g",
                "1/4 moisturizing cream beauty bar pack",
                "340111",
                "8901030711012",
                cat_personal.id,
                uom_pcs.id,
                165.00,
                198.00,
                50.0,
                100.0,
            ),
            (
                "SKU-SOAP-LUX-3X100G",
                "Lux Rose & Vitamin E Beauty Bar 3x100g",
                "Fragrant rose beauty soap multi-pack",
                "340111",
                "8901030722018",
                cat_personal.id,
                uom_pcs.id,
                105.00,
                128.00,
                60.0,
                120.0,
            ),
            (
                "SKU-SOAP-LIFE-4X125G",
                "Lifebuoy Total Germ Protection Soap 4x125g",
                "Silver shield formula germ protection bar",
                "340111",
                "8901030733014",
                cat_personal.id,
                uom_pcs.id,
                120.00,
                145.00,
                60.0,
                120.0,
            ),
            (
                "SKU-DET-SURF-2KG",
                "Surf Excel Easy Wash Detergent Powder 2kg",
                "Super fine detergent powder bag",
                "340220",
                "8901030611015",
                cat_personal.id,
                uom_pcs.id,
                240.00,
                285.00,
                50.0,
                100.0,
            ),
            (
                "SKU-DET-SURF-MATIC-2L",
                "Surf Excel Matic Front Load Liquid 2L",
                "Liquid detergent for washing machine",
                "340220",
                "8901030622011",
                cat_personal.id,
                uom_pcs.id,
                380.00,
                450.00,
                30.0,
                60.0,
            ),
            (
                "SKU-DET-RIN-BAR-4X250G",
                "Rin Detergent Bar 4x250g Multi-pack",
                "Bright clean laundry detergent soap bar",
                "340119",
                "8901030633017",
                cat_personal.id,
                uom_pcs.id,
                68.00,
                84.00,
                70.0,
                140.0,
            ),
            (
                "SKU-PST-COLG-MAX-300G",
                "Colgate MaxFresh Spicy Fresh Gel 300g",
                "Cooling crystal freshening gel paste",
                "330610",
                "8901314011013",
                cat_personal.id,
                uom_pcs.id,
                160.00,
                195.00,
                40.0,
                80.0,
            ),
            (
                "SKU-SHM-CLINIC-650ML",
                "Clinic Plus Strong & Long Shampoo 650ml",
                "Milk protein daily nourishing shampoo",
                "330510",
                "8901030511018",
                cat_personal.id,
                uom_pcs.id,
                275.00,
                335.00,
                35.0,
                70.0,
            ),
            # Category: Packaged Foods & Sauces
            (
                "SKU-NDL-MAGG-MAS-560G",
                "Maggi 2-Minute Masala Noodles 8-Pack 560g",
                "Classic favorite masala instant noodles",
                "190230",
                "8901058861010",
                cat_packaged.id,
                uom_pcs.id,
                92.00,
                112.00,
                90.0,
                180.0,
            ),
            (
                "SKU-NDL-YIPP-MAS-480G",
                "Sunfeast YiPPee! Magic Masala Noodles 8-Pack",
                "Non-sticky round block masala noodles",
                "190230",
                "8901725191016",
                cat_packaged.id,
                uom_pcs.id,
                85.00,
                104.00,
                70.0,
                140.0,
            ),
            (
                "SKU-SAU-KISS-KET-1KG",
                "Kissan Fresh Tomato Ketchup Squeezy 1kg",
                "100% real ripe tomato ketchup pouch",
                "210320",
                "8901030811019",
                cat_packaged.id,
                uom_pcs.id,
                110.00,
                134.00,
                40.0,
                80.0,
            ),
            (
                "SKU-SAU-MAGG-HOT-1KG",
                "Maggi Hot & Sweet Chilli Tomato Sauce 1kg",
                "Tangy tomato chilli blend bottle",
                "210320",
                "8901058871019",
                cat_packaged.id,
                uom_pcs.id,
                125.00,
                152.00,
                35.0,
                70.0,
            ),
            (
                "SKU-JAM-KISS-MIX-1KG",
                "Kissan Mixed Fruit Jam Jar 1kg",
                "8 fruit pulp spread gourmet jam",
                "200799",
                "8901030822015",
                cat_packaged.id,
                uom_pcs.id,
                210.00,
                255.00,
                30.0,
                60.0,
            ),
            (
                "SKU-PAS-DELM-PEN-500G",
                "Del Monte Penne Rigate Durum Wheat Pasta 500g",
                "100% Italian durum wheat semolina pasta",
                "190219",
                "8901248101019",
                cat_packaged.id,
                uom_pcs.id,
                95.00,
                118.00,
                40.0,
                80.0,
            ),
        ]

        seeded_products: dict[str, Product] = {}
        for pdata in products_data:
            sku, name, desc, hsn, barcode, cat_id, uom_id, cost, wholesale, r_pt, r_qty = pdata
            prod = upsert_product(
                db, sku, name, desc, hsn, barcode, cat_id, uom_id, cost, wholesale, r_pt, r_qty
            )
            seeded_products[sku] = prod

        # 7. Base Product UOM Conversions (1 Case = 24 Pieces)
        print("-> Seeding UOM Conversions...")
        for sku in ["SKU-NDL-MAGG-MAS-560G", "SKU-BIS-PARLEG-800G", "SKU-OIL-FORT-1L"]:
            prod = seeded_products[sku]
            existing_conv = db.execute(
                select(ProductUOMConversion).where(
                    ProductUOMConversion.product_id == prod.id,
                    ProductUOMConversion.from_uom_id == uom_case.id,
                    ProductUOMConversion.to_uom_id == uom_pcs.id,
                )
            ).scalar_one_or_none()
            if not existing_conv:
                conv = ProductUOMConversion(
                    product_id=prod.id,
                    from_uom_id=uom_case.id,
                    to_uom_id=uom_pcs.id,
                    factor=24.0,
                )
                db.add(conv)
                db.flush()

        # 8. RBAC: 5 Roles & Starting Permission Matrix
        print("-> Seeding RBAC Roles & Permissions Matrix...")
        perms_data = [
            ("inventory:view", "View real-time stock balances, batches, and movements"),
            ("inventory:manage", "Create, adjust, transfer, and receive stock batches"),
            ("orders:create", "Create sales and purchase orders"),
            ("orders:view", "View all order pipelines and histories"),
            ("orders:approve", "Approve returns, cancel or modify orders"),
            ("invoices:create", "Generate and issue GST tax invoices"),
            ("invoices:view", "View invoices and payment history"),
            ("payments:record", "Record incoming and outgoing payments against balances"),
            ("reports:view", "Access wholesale analytics and compliance reports"),
            ("staff:view", "View staff members and role assignments"),
            ("staff:manage", "Invite staff, modify roles, and configure permissions"),
            ("settings:manage", "Manage system, business profile, and user settings"),
            ("audit:view", "Inspect administrative audit logs and changes"),
        ]
        seeded_perms: dict[str, Permission] = {}
        for code, desc in perms_data:
            seeded_perms[code] = get_or_create_permission(db, code, desc)

        # 5 Default Roles
        role_owner = get_or_create_role(
            db, "Owner", "Full uninhibited root access across the entire organization"
        )
        role_manager = get_or_create_role(
            db, "Manager", "Warehouse and commercial operations management"
        )
        role_sales = get_or_create_role(
            db, "Sales Staff", "Sales order processing and catalog inquiry handling"
        )
        role_wh = get_or_create_role(
            db, "Warehouse Staff", "Receiving, packing, batch inspection, and dispatch"
        )
        role_acc = get_or_create_role(
            db, "Accountant", "Invoicing, payment netting, credit limits, and tax audits"
        )

        # Permission matrix mapping
        role_matrix = {
            role_owner.id: list(seeded_perms.keys()),  # All permissions
            role_manager.id: [
                "inventory:view",
                "inventory:manage",
                "orders:create",
                "orders:view",
                "orders:approve",
                "invoices:view",
                "reports:view",
                "audit:view",
            ],
            role_sales.id: ["inventory:view", "orders:create", "orders:view", "invoices:view"],
            role_wh.id: ["inventory:view", "inventory:manage", "orders:view"],
            role_acc.id: [
                "orders:view",
                "invoices:create",
                "invoices:view",
                "payments:record",
                "reports:view",
                "audit:view",
            ],
        }

        for role_id, perm_codes in role_matrix.items():
            for code in perm_codes:
                sync_role_permission(db, role_id, seeded_perms[code].id)

        # 9. Stock Batches (Healthy Stock + Deliberate Low-Stock Items)
        print("-> Seeding Stock Batches & Low-Stock Alerts...")
        # 3 products deliberately UNDER reorder_point:
        # 1. Nescafe 200g: reorder_point=25, seeded qty=6 across warehouses
        # 2. Taj Mahal Tea 500g: reorder_point=30, seeded qty=8
        # 3. Kissan Mixed Fruit Jam 1kg: reorder_point=30, seeded qty=5
        # 4. Del Monte Penne Pasta: reorder_point=40, seeded qty=10
        low_stock_skus = {
            "SKU-COF-NESC-200G": 6.0,
            "SKU-TEA-TAJ-500G": 8.0,
            "SKU-JAM-KISS-MIX-1KG": 5.0,
            "SKU-PAS-DELM-PEN-500G": 10.0,
        }

        exp_future_1y = date.today() + timedelta(days=365)
        exp_future_2y = date.today() + timedelta(days=730)

        for sku, prod in seeded_products.items():
            if sku in low_stock_skus:
                # Seed deliberately below reorder_point
                upsert_stock_batch(
                    db,
                    prod.id,
                    wh_bhiwandi.id,
                    f"BATCH-LOW-{sku[-8:]}",
                    low_stock_skus[sku],
                    exp_future_1y,
                )
            else:
                # Healthy stock distributed between Bhiwandi and Vashi
                upsert_stock_batch(
                    db,
                    prod.id,
                    wh_bhiwandi.id,
                    f"B-BHI-{sku[-8:]}-01",
                    prod.reorder_qty * 1.5,
                    exp_future_2y,
                )
                upsert_stock_batch(
                    db,
                    prod.id,
                    wh_vashi.id,
                    f"B-VAS-{sku[-8:]}-02",
                    prod.reorder_qty * 0.8,
                    exp_future_2y,
                )

        # 10. Business Settings Profile
        print("-> Seeding Business Profile Settings...")
        biz = db.execute(select(BusinessSettings)).scalar_one_or_none()
        if not biz:
            biz = BusinessSettings(
                business_name="WareFlow Global Distribution Pvt Ltd",
                gstin="27AAACW9988H1Z4",
                fssai_license_no="11518018000999",
                fssai_expiry_date=date(2028, 12, 31),
                address="Plot No. 12/B, Sector 19-C, APMC Market-II, Vashi, Navi Mumbai, MH 400703",
                phone="+912227891234",
                email="contact@wareflow.in",
            )
            db.add(biz)
            db.flush()

        db.commit()
        print("✅ Database seeding complete!")


if __name__ == "__main__":
    seed_database()
