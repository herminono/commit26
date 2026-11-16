# PakaiLagi
#### A Student-to-Student Marketplace for Buying and Renting Campus Essentials
### 1. Project Information
**Project Name:** PakaiLagi
**Team Name:** Tim WD-1

**Team Members:**
- Rico Hermino (leader)
- Felissa Novenia

### 2. Project Overview
PakaiLagi is a web-based marketplace designed to help university students buy, sell, and, rent academic essentials within their campus community.
Students often need textbooks, electronic devices, laboratory equipment, and other academic supplies that may only be used for a limited period of time. Purchasing these items at full price can be expensive, while unused items owned by other students who are willing to sell/rent it may still be in good condition.
PakaiLagi aims to address this problem by providing a platform where students can discover affordable secondhand products or rent items directly from other students.
In addition to improving accessibility and affordability, PakaiLagi encourages the reuse of existing items to reduce unnecessary purchases.

### 3. Main Features
#### User Authentication and Authorization
- User registration and login.
- Two account roles: Buyer and Merchant.
- JWT-based authentication.
- Role-based access to specific features.
- Password hashing and salting for account security.

#### Product Marketplace
- Browse products listed by merchants.
- Search for products by name.
- View product details, including price, description, condition, and merchant information.
- Support for two transaction types: secondhand and rental.

#### Buyer Features
- Add products to a wishlist.
- Add products to a shopping cart.
- Move products between the wishlist and cart.
- Remove saved products.
- View a checkout summary containing selected products and estimated prices.
- Access merchant contact information through email to arrange transactions.

#### Merchant Features
- Add new product listings.
- Provide product names, prices, description, conditions, transaction types, and image URLs.
- View products listed by the authenticated merchant.
- Delete products owned by the merchant.

#### Manual Checkout
PakaiLagi uses a manual transaction process. Buyers can review their selected products and contact merchants to discuss availability, rental duration, payment arrangements, and product delivery.
The platform does not currently process payments or automatically generate orders.

### 4. Technologies Used
- Python: Backend programming language
- Flask: Web framework and REST API development
- Flask-SQLAlchemy: Object-Relational Mapping (ORM)
- PostgreSQL: Relational database
- Neon: Cloud-hosted PostgreSQL database
- Flask-JWT-Extended: JWT authentication and authorization
- Werkzeug: Password hashing, salting, and verification
- HTML: Website structure
- CSS: Website styling and responsive layout
- JavaScript: Frontend interaction and API communication
- Jinja2: Render HTML templates
- Vercel: Web application deployment
- Github: Version control and source code hosting.

### 5. Project Structure
```
PakaiLagi/
 |-- main.py > contains the Flask application, database models, authentication logic, and REST API endpoints.
 |-- requirements.txt
 |-- .gitignore
 |-- README.md
 |-- templates/
 |   |-- index.html > contains the website's HTML structure.
 |-- static/
     |-- app.js > manages frontend interactions and API requests.
     |-- style.css > contains the website's visual styling and responsive design.
```

### 6. Installation and Setup
#### Prerequiesites
Make sure the following are available:
- Python 3
- Git
- A PostgreSQL database, such as Neon
- A code editor
#### Step 1: Clone
```
git clone https://github.com/herminono/commit26.git
cd commit26
```
#### Step 2: Create Virtual Environment
`python -m venv .venv`
Activate the virtual environment.
##### WIndows:
`.venv\Scripts\activate`
##### macOS/Linux:
`source .venv/bin/activate`
#### Step 3: Install Dependencies
`pip install -r requirements.txt`
#### Step 4: Configure Environment Variables
Create a .env file in the project's root directory.
Add the following variables:
```
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require
JWT_SECRET_KEY=YOUR_SECRET_KEY
```
###### Note: JWT_SECRET_KEY is created manually. Replace the placeholder values with your own database credentials.
#### Step 5: Prepare the Database
Ensure that the PostgreSQL database contains the required tables and constraints.
The application uses three main tables:
- users > Stores registered users and their account roles.
- items > Stores product listing and their associated merchants
- user_items > Stores buyer wishlist and cart records.
Database initialization or schema migration may be required when setting up a new database.
#### Step 6: Run the Application
`python main.py`
Open the local address displayed by Flask in your browser. By default, this is usually
`http://127.0.0.1:5000`
### 7. How to Use
#### As a Buyer
1. Register an account and select Buyer
2. Log in using the registered credentials.
3. Open the Explore page to browse available products.
4. Select a product to view its details.
5. Add products to the wishlist or shopping cart.
6. Open the Cart page to review the checkout summary.
7. Contact the merchant to arrange transaction.
#### As a Merchant
1. Register an account and select Merchant.
2. Log in to access the Merchant Dashboard.
3. Complete the product listing form.
4. Submit the product to make it available in the marketplace.
5. View or delete existing product listings from the dashboard.

### 8. AI Assistance and Third-Party Resources
AI tools, including ChatGPT, were used as assistant during the project.
AI assistance was involved in activities such as:
- Supporting frontend development, helped to comprehend syntaxes, and UI/UX improvements.
- Providing explanations of unfamiliar concepts such as integrating Flask to JavaScript to HTML, and JavaScript syntaxes.
This project was not built from a pre-existing application template.

#### Third-Party Resources:
- Google Fonts for website typography.
- Externally hosted images for product listing and selected website visuals.
- Open-source Python libraries and frameworks listed in the technological section.

### 9. Project Limitations
- No integrated payment gateway: payment are arranged manually between buyer and merchant.
- No automatic order processing: the platform does not create or manage confirmed transacrions.
- Manual rental arrangements
- No built-in messaging system: buyers contact merchants through provided contact information.
- No direct image uploading: merchants have to provide image URLs
- No inventory management

### 10. Future Improvements
- Integrated messaging between buyers and merchants.
- Product categories and advanced search filters.
- Order management and transaction history.
- Product availability tracking.
- Improved accessibility and responsive design.

### 11. Deployment
PakaiLagi is designed to be deployed using Vercel, with Neon PostgreSQL serving as its cloud database.
Website: <https://commit26.vercel.app>
