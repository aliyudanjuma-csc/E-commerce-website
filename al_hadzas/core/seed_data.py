"""
core/seed_data.py
--------------------
Populates the in-memory DataStore with a demo admin, two vendors, a
buyer, and a starter catalogue so the coursework demo is immediately
browsable/searchable without any manual setup.

Demo login credentials (printed to console on startup too):
    Admin  : admin@alhadzas.com   / Admin#1234
    Vendor : amina@alhadzas.com   / Vendor#1234   (Amina Textiles, Ghana)
    Vendor : kwame@alhadzas.com   / Vendor#1234   (Kwame & Sons, Nigeria)
    Buyer  : buyer@alhadzas.com   / Buyer#1234
"""

from core.data_store import STORE, User, Vendor, Product, next_id
from core.security import hash_password


def _make_user(name: str, email: str, password: str, role: str) -> User:
    pw_hash, salt = hash_password(password)
    user = User(id=next_id("USR"), name=name, email=email,
                password_hash=pw_hash, salt=salt, role=role)
    STORE.add_user(user)
    return user


def seed() -> None:
    if STORE.users:
        return  # already seeded (e.g. hot reload)

    admin = _make_user("AL-HADZAS Admin", "admin@alhadzas.com", "Admin#1234", "admin")

    amina_user = _make_user("Amina Boateng", "amina@alhadzas.com", "Vendor#1234", "vendor")
    amina_vendor = Vendor(id=next_id("VEN"), user_id=amina_user.id,
                           business_name="Amina Textiles", country="Ghana", verified=True)
    STORE.add_vendor(amina_vendor)

    kwame_user = _make_user("Kwame Boateng", "kwame@alhadzas.com", "Vendor#1234", "vendor")
    kwame_vendor = Vendor(id=next_id("VEN"), user_id=kwame_user.id,
                           business_name="Kwame & Sons Atelier", country="Nigeria", verified=True)
    STORE.add_vendor(kwame_vendor)

    _make_user("Demo Buyer", "buyer@alhadzas.com", "Buyer#1234", "buyer")

    products = [
        dict(name="Kente Wrap Dress", fabric="Handwoven Kente cotton",
             country_of_origin="Ghana", occasion="Wedding / Formal", price=189.00,
             vendor=amina_vendor,
             description="A vibrant handwoven Kente wrap dress. Kente originates from "
                          "the Ashanti people of Ghana; each color and pattern carries "
                          "symbolic meaning, traditionally reserved for royalty and "
                          "special ceremonies."),
        dict(name="Ankara Print Maxi Skirt", fabric="Ankara wax-print cotton",
             country_of_origin="Nigeria", occasion="Everyday wear", price=59.00,
             vendor=kwame_vendor,
             description="A bold Ankara wax-print maxi skirt, tailored for everyday wear. "
                          "Ankara fabric is beloved across West Africa for its bright, "
                          "geometric wax-resist patterns."),
        dict(name="Men's Agbada Set", fabric="Brocade with hand embroidery",
             country_of_origin="Nigeria", occasion="Wedding / Owambe", price=310.00,
             vendor=kwame_vendor,
             description="A traditional three-piece Agbada set with hand embroidery, worn "
                          "by Yoruba men for weddings and major celebrations as a symbol "
                          "of status and dignity."),
        dict(name="Dashiki Shirt", fabric="Cotton Dashiki print",
             country_of_origin="Ghana", occasion="Everyday / Festival", price=45.00,
             vendor=amina_vendor,
             description="A classic Dashiki shirt with an embroidered v-neck collar, worn "
                          "across West Africa as an expression of cultural pride at "
                          "festivals and everyday wear alike."),
        dict(name="Adire Tie-Dye Kaftan", fabric="Hand-dyed Adire cotton",
             country_of_origin="Nigeria", occasion="Everyday / Cultural events", price=75.00,
             vendor=kwame_vendor,
             description="A flowing kaftan made from Adire, a resist-dye textile "
                          "hand-crafted by Yoruba women using indigo dye and traditional "
                          "tie-dye or starch-resist techniques."),
        dict(name="Bogolan Mud Cloth Jacket", fabric="Bogolan (mud cloth) cotton",
             country_of_origin="Mali", occasion="Statement / Outerwear", price=140.00,
             vendor=amina_vendor,
             description="A structured jacket made from Bogolan, a Malian mud cloth "
                          "fabric hand-dyed using fermented mud and plant dyes in "
                          "patterns that traditionally record proverbs and history."),
        dict(name="Kaftan Boubou Gown", fabric="Bazin riche cotton",
             country_of_origin="Senegal", occasion="Wedding / Formal", price=165.00,
             vendor=amina_vendor,
             description="An elegant Boubou gown in richly starched Bazin fabric, a "
                          "formal wear staple across Senegal and the wider Sahel region."),
        dict(name="Kitenge Wrap Set", fabric="Kitenge printed cotton",
             country_of_origin="Kenya", occasion="Everyday / Beach", price=68.00,
             vendor=kwame_vendor,
             description="A breezy two-piece Kitenge wrap set in East African printed "
                          "cotton, popular for its vivid colors and everyday comfort."),
    ]

    for p in products:
        vendor = p.pop("vendor")
        product = Product(
            id=next_id("PRD"),
            vendor_id=vendor.id,
            name=p["name"],
            description=p["description"],
            fabric=p["fabric"],
            country_of_origin=p["country_of_origin"],
            occasion=p["occasion"],
            price=p["price"],
            sizes=["S", "M", "L", "XL", "Made-to-Measure"],
            stock=25,
        )
        STORE.add_product(product)

    print("=" * 60)
    print("AL-HADZAS COLLECTIONS demo data seeded. Login with:")
    print("  Admin  : admin@alhadzas.com   / Admin#1234")
    print("  Vendor : amina@alhadzas.com   / Vendor#1234")
    print("  Vendor : kwame@alhadzas.com   / Vendor#1234")
    print("  Buyer  : buyer@alhadzas.com   / Buyer#1234")
    print("=" * 60)
