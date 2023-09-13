# Library Management System API
This is a RESTFUL API for a library service. It allows users to borrow and return books, make payments for borrowed books, and receive notifications about overdue books and successful payments.

## Requirements
- Python 3.9 or later
- Docker and Docker Compose
- Postgres DB (or change settings for your DB)
## SetUp
**Local**
1. Clone this repository: git clone https://github.com/IvanGLS/library_service_project
2. cd library_service_project
3. Install virtual environment and requirements
```
python -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
4. Create a .env file in the root directory of the project and add the required environment variables (see .env.example for reference).
   
5. Access the API at http://localhost:8000.

**Docker image**

1. Run docker-compose up to start the development server and other required services.
```
2. docker-compose up --build
```
3. Access the API at http://localhost:8000.

**Test data**
```
SECRET_KEY=r1@a@r8*#!uzz8zb*97cd(mxmg_ko#=%v@g+_6g0j9t8oiy00y
TELEGRAM_BOT_TOKEN=5836978281:AAERmPqAES9jdAn08FX9cORwmSTrYb-wKvQ
TELEGRAM_CHAT_ID=-847746096
```

## API Endpoints

### User API
- POST /user/ - Create a new user
- POST /user/token/ - Obtain a JSON web token pair
- POST /user/token/refresh/ - Refresh an access token
- POST /user/token/verify/ - Verify an access token
- GET /user/me/ - Get the authenticated user's profile

**Authentication**
> To access the API, a user needs to authenticate themselves by providing a valid JSON web token (JWT) in the Authorization header of their HTTP request. The JWT is obtained by calling the /user/token/ endpoint with valid user credentials.

### Library API
- GET /books/ - List all books
- GET /books/<int:pk>/ - Retrieve a book by ID
- GET /borrowings/ - List all borrowings
- GET /borrowings/<int:pk>/ - Retrieve a borrowing by ID
- POST /borrowings/initiate_payment/<int:payment_id>/ - Initiate payment for a borrowing
- POST /borrowings/<int:pk>/return/ - Return a borrowed book
- GET /payments/ - List all payments
- GET /payments/<int:pk>/ - Retrieve a payment by ID
- POST /payments/success/ - Payment success callback
- POST /payments/cancel/ - Payment cancel callback

## Telegram sender
Implemented telegram sender 

- when borrowing is created
- when successful payment
- when borrowing is overdue(scheduled celery task)
> Create bot instruction https://core.telegram.org/bots  
 Find CHAT_ID bot (https://t.me/getmyid_bot)


## Celery Tasks
The API uses Celery for background tasks. The following tasks are available:

- library_service_api.tasks.run_sync_with_api: *Sends a Telegram message when a borrowing is overdue.*

- library_service_api.tasks.check_expired_sessions: *scheduled task for checking Stripe Session for expiration*


## Credits
This API was created by ©IvanGLS
