from itsdangerous import NoneAlgorithm
from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity,jwt_required
import os
from dotenv import load_dotenv
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app=Flask(__name__)

class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 3,
    "max_overflow": 2,
    "pool_timeout": 30
}
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

db = SQLAlchemy(model_class=Base)
db.init_app(app)

jwt = JWTManager(app)

#User Table
class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True,nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('buyer', 'merchant')",
            name="check_user_role"
        ),
    )
    def to_dict(self):
        return{
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }

#Item Table
class Item(db.Model):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(1500), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    condition: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="check_item_price"),
        CheckConstraint(
            "transaction_type IN ('secondhand', 'rental')",
            name ="check_transaction_type"),
    )
    merchant = relationship("User")
    def to_dict(self):
        return{
            "id": self.id,
            "merchant_id": self.merchant_id,
            "seller": self.merchant.name,
            "name": self.name,
            "price": str(self.price),
            "description": self.description,
            "image_url": self.image_url,
            "transaction_type": self.transaction_type,
            "condition": self.condition
        }

#Shopping Cart and Wishlist Table
class UserItem(db.Model):
    __tablename__ = "user_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"),nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "buyer_id", "item_id",
            name="unique_buyer_item"
        ),
        CheckConstraint(
            "status IN ('cart', 'wishlist')",
            name="check_item_status"
        ),
    )
    def to_dict(self):
        return{
            "id": self.id,
            "buyer_id": self.buyer_id,
            "item_id": self.item_id,
            "status": self.status,
        }

#Create all the tables
with app.app_context():
    db.create_all()
    print(f"Database connectted to {db.engine.url.database}")

#Register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify(error="Name is required."), 400
    name = name.strip()
    if len(name) > 100:
        return jsonify(error="Name is too long."), 400
    if not isinstance(email,str) or not email.strip():
        return jsonify(error="Email is required."), 400

    email = email.strip().lower()
    if not isinstance(password, str) or len(password) < 6:
        return jsonify(error="Password must have at least 6 characters."), 400

    if role not in ["buyer", "merchant"]:
        return jsonify(error="Invalid role."), 400
    existing_user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if existing_user is not None:
        return jsonify(error="Email is already registered."), 409

    new_user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Email already registered."), 409

    return jsonify(
        message="Registration successful.",
        user = new_user.to_dict()
    ), 201

#Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email,str) or not isinstance(password,str):
        return jsonify(error="Email and Password are required."), 400

    user = db.session.execute(
        db.select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()


    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify(error="Invalid email or password."), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify(message="Login successful.", access_token=access_token, user=user.to_dict()), 200

#See items
@app.route("/items", methods=["GET"])
def get_items():
    search = request.args.get("search","").strip()
    query=db.select(Item)
    if search:
        query = query.where(Item.name.ilike(f"%{search}%"))
    query = query.order_by(Item.id.desc())
    items = db.session.execute(query).scalars().all()
    return jsonify(items=[item.to_dict() for item in items]), 200

#Add item(merchant)
@app.route("/items", methods=["POST"])
@jwt_required()
def add_item():
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role!="merchant":
        return jsonify(error="Merchant access required."), 403

    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400
    name = data.get("name")
    description = data.get("description")
    image_url = data.get("image_url")
    if not all(
        isinstance(value, str) and value.strip()
        for value in [name, description, image_url]
    ):
        return jsonify(error="Invalid item information."), 400
    if len(name) > 250 or len(image_url) > 1000:
        return jsonify(error="Name or image url is too long."), 400

    if not image_url.startswith(("https://", "http://")):
        return jsonify(error="Invalid image URL."), 400

    transaction_type = data.get("transaction_type")
    condition = data.get("condition")

    if transaction_type not in ["secondhand", "rental"]:
        return jsonify(error="Invalid transaction type."), 400
    if not isinstance(condition,str) or not condition.strip():
        return jsonify(error="Condition is required."), 400
    condition = condition.strip()
    if len(condition) > 100:
        return jsonify(error="Condition too long."), 400

    try:
        price = Decimal(str(data["price"]))
        if not price.is_finite() or price < 0:
            raise ValueError()
        if price != price.quantize(Decimal("0.01")):
            raise ValueError()
        if price >= Decimal("10000000000"):
            raise ValueError()
    except (KeyError, InvalidOperation, ValueError, TypeError):
        return jsonify(error="Invalid price format."), 400

    new_item = Item(
        merchant_id=user_id,
        name=name.strip(),
        price=price,
        description=description.strip(),
        image_url=image_url.strip(),
        transaction_type=transaction_type,
        condition=condition,
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(message="Item added successfully.", item=new_item.to_dict()), 201

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        return jsonify(error="Item not found."), 404
    return jsonify(item=item.to_dict()), 200

#Edit item(merchant(
@app.route("/items/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_item(item_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "merchant":
        return jsonify(error="Merchant access required."), 403

    item = db.session.get(Item,item_id)

    if item is None:
        return jsonify(error="Item not found."), 404
    if item.merchant_id != user_id:
        return jsonify(error="This is not your item."), 403

    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400

    allowed_fields = {"name", "description", "image_url", "price", "transaction_type", "condition"}
    if not data or not set(data).issubset(allowed_fields):
        return jsonify(error="Invalid update fields."), 400

    for field in ["name", "description", "image_url"]:
        if field in data:
            value = data[field]
            if not isinstance(value,str) or not value.strip():
                return jsonify(error=f"Invalid {field}."), 400

            if field == "name" and len(value) > 250:
                return jsonify(error="Name too long."), 400

            if field == "image_url":
                if len(value) > 1000:
                    return jsonify(error="Image url is too long."), 400
                if not value.startswith(("https://", "http://")):
                    return jsonify(error="Invalid image URL."), 400

            setattr(item,field,value.strip())
    if "transaction_type" in data:
        transaction_type = data["transaction_type"]
        if transaction_type not in ["secondhand", "rental"]:
            return jsonify(error="Invalid transaction type."), 400
        item.transaction_type = transaction_type
    if "condition" in data:
        condition = data["condition"]
        if (
                not isinstance(condition, str)
                or not condition.strip()
                or len(condition.strip()) > 100
        ):
            return jsonify(error="Invalid condition."), 400

        item.condition = condition.strip()
    if "price" in data:
        try:
            price = Decimal(str(data["price"]))
            if not price.is_finite() or price < 0:
                raise ValueError()
            if price != price.quantize(Decimal("0.01")):
                raise ValueError()
            if price >= Decimal("10000000000"):
                raise ValueError()
        except (InvalidOperation, ValueError, TypeError):
            return jsonify(error="Invalid price format."), 400

        item.price = price
    db.session.commit()

    return jsonify(
        message="Item updated successfully.",
        item=item.to_dict()
    ),200

#Delete item(merchant)
@app.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "merchant":
        return jsonify(error="Merchant access required."), 403

    item = db.session.get(Item,item_id)
    if item is None:
        return jsonify(error="Item not found."), 404

    if item.merchant_id != user_id:
        return jsonify(error="This is not your item."), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify(message="Item deleted successfully."), 200

#Add item(buyer)
@app.route("/user-items", methods=["POST"])
@jwt_required()
def add_user_item():
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "buyer":
        return jsonify(error="Buyer access required."), 403

    data = request.get_json(silent=True)

    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400

    item_id = data.get("item_id")
    status = data.get("status")
    if type(item_id) is not int or item_id <= 0:
        return jsonify(error="Item id is invalid."), 400
    if status not in ["cart", "wishlist"]:
        return jsonify(error="Item status is invalid."), 400

    item = db.session.get(Item,item_id)
    if item is None:
        return jsonify(error="Item not found."), 404

    existing = db.session.execute(
        db.select(UserItem).where(
            UserItem.buyer_id == user_id,
            UserItem.item_id == item_id
        )).scalar_one_or_none()

    if existing:
        if existing.status == status:
            return jsonify(error="Item already in this status."), 409
        return jsonify(error="Item already saved. Use PATCH to change its status."), 409

    new_user_item = UserItem(
        buyer_id = user_id,
        item_id = item_id,
        status = status
    )

    try:
        db.session.add(new_user_item)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Item already saved."), 409

    return jsonify(
        message="Item saved successfully.",
        user_item=new_user_item.to_dict()
    ), 201

#See item (buyer)
@app.route("/user-items", methods=["GET"])
@jwt_required()
def get_user_items():
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "buyer":
        return jsonify(error="Buyer access required."), 403

    status = request.args.get("status")
    if status is not None and status not in ["cart", "wishlist"]:
        return jsonify(error="Item status is invalid."), 400

    query = db.select(UserItem).where(UserItem.buyer_id == user_id)
    if status:
        query = query.where(UserItem.status == status)

    records = db.session.execute(query).scalars().all()
    result = []
    for record in records:
        item = db.session.get(Item, record.item_id)
        if item is None:
            continue
        record_data = record.to_dict()
        product_data = item.to_dict()
        if record.status == "cart":
            product_data["seller_email"] = item.merchant.email
        record_data["product"] = product_data
        result.append(record_data)
    return jsonify(user_items=result),200

#Move between cart and wishlist
@app.route("/user-items/<int:record_id>", methods=["PATCH"])
@jwt_required()
def update_user_item(record_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "buyer":
        return jsonify(error="Buyer access required."), 403
    record = db.session.get(UserItem,record_id)
    if record is None:
        return jsonify(error="Record not found."), 404
    if record.buyer_id != user_id:
        return jsonify(error="Access denied."), 403

    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error="JSON body is required."), 400

    new_status = data.get("status")
    if new_status not in ["cart", "wishlist"]:
        return jsonify(error="Invalid status."), 400

    record.status = new_status
    db.session.commit()

    return jsonify(message="Item updated successfully.",
                   user_item=record.to_dict()), 200

#Remove item from cart/wishlist
@app.route("/user-items/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_user_item(record_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "buyer":
        return jsonify(error="Buyer access required."), 403
    record = db.session.get(UserItem,record_id)

    if record is None:
        return jsonify(error="Record not found."), 404
    if record.buyer_id != user_id:
        return jsonify(error="Access denied."), 403

    db.session.delete(record)
    db.session.commit()
    return jsonify(message="Item deleted successfully.",), 200

@app.route("/merchant/items", methods=["GET"])
@jwt_required()
def get_merchant_items():
    user_id = int(get_jwt_identity())
    user = db.session.get(User,user_id)
    if user is None or user.role != "merchant":
        return jsonify(error="Merchant access required."), 403
    items = db.session.execute(
        db.select(Item).where(Item.merchant_id == user_id)
        .order_by(Item.id.desc())
    ).scalars().all()
    return jsonify(items=[item.to_dict() for item in items]), 200

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)