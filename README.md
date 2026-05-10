# PocketPay Server

PocketPay Server is a FastAPI backend for a digital wallet and payment platform. It provides user authentication, wallet balance management, peer-to-peer transfers, mobile recharge, bill payments, donations, QR generation, notifications, and an admin dashboard.

## Features

- User registration, login, logout, password reset, OTP verification, and token refresh
- JWT-based authentication with optional two-factor authentication flows
- Wallet balance lookup, send money, and transaction detail APIs
- Mobile recharge operator management and recharge processing
- Bill provider listing and bill payment processing
- Donation organization listing and donation request workflows
- Transaction history and notification APIs
- QR code generation for payment-related flows
- Admin dashboard for users, wallets, transactions, refunds, notifications, and admin management

## Tech Stack

- **FastAPI** for the API application
- **SQLAlchemy** for ORM and database access
- **SQLite** for local development storage
- **Pydantic** for request and response validation
- **python-jose** for JWT handling
- **Passlib bcrypt** for password hashing
- **Jinja2 templates** and static assets for the admin dashboard
- **Cloudinary** support for image uploads

## Project Structure

```text
PocketPay-Server/
|-- admin/                 # Admin authentication and management routes
|-- app/
|   |-- constants/         # Environment and shared constants
|   |-- core/              # Database configuration
|   |-- model/             # SQLAlchemy models
|   |-- router/            # API route modules
|   |-- schema/            # Pydantic schemas
|   |-- services/          # Business logic
|   |-- templates/         # Email, SMS, and push templates
|   `-- utils/             # Auth, hashing, notification, and helper utilities
|-- static/                # Admin dashboard static files
|-- templates/             # Admin dashboard HTML templates
|-- run.py                 # Local development runner
|-- requirements.txt       # Python dependencies
`-- README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip`
- A virtual environment tool such as `venv`

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/rifatsoftdev/PocketPay-Server.git
   cd PocketPay-Server
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   On Windows:

   ```bash
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and configure the required values:

   ```env
   EMAIL_ADDRESS=your-email@example.com
   EMAIL_PASSWORD=your-email-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False

   GOOGLE_CLIENT_ID=your-google-client-id

   SECRET_KEY=change-this-secret-key
   ALGORITHM=HS256
   ACCESS_EXPIRE=30
   REFRESH_EXPIRE=10080

   OTP_TOKEN_EXPIRE_MIN=5
   PASS_RST_TOKEN_EXPIRE_MIN=15

   NEW_USER_REWARD_WITH_REFERRAL=0
   NEW_USER_REWARD_WITH_NO_REFERRAL=0
   USER_REFERRAL_REWARD=0
   SERVICE_CHARGE=0

   VERSION=1.0.0
   DEBUG=True

   CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
   CLOUDINARY_API_KEY=your-cloudinary-api-key
   CLOUDINARY_API_SECRET=your-cloudinary-api-secret

   SALT=change-this-salt
   SERVICE_ACCOUNT_PATH=path/to/firebase-service-account.json
   ```

5. Start the development server:

   ```bash
   python run.py
   ```

   The local runner binds to your machine's network IP on port `8000`. You can also run Uvicorn directly:

   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## API Documentation

After starting the server, open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Admin login: `http://localhost:8000/admin/login`

## Main API Routes

### Authentication

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/google-login`
- `POST /auth/logout`
- `POST /auth/new-access-token`
- `POST /auth/send-otp`
- `POST /auth/verify-otp`
- `POST /auth/reset-password`
- `POST /auth/set-password`
- `POST /auth/change-password`
- `POST /auth/logout-all`
- `POST /auth/delete-account`
- `POST /auth/cancel-delete`

### User

- `GET /user/profile`
- `GET /user/edit-info`
- `POST /user/profile/update`
- `POST /user/image-upload`

### Wallet

- `GET /wallet/balance`
- `POST /wallet/sent-money`
- `GET /wallet/transaction/{transaction_id}`

### Transaction History

- `GET /history/all-transactions`
- `POST /history/all-notifications`

### Mobile Recharge

- `GET /recharge/operators`
- `POST /recharge/recharge`
- `POST /recharge/new-operator`
- `POST /recharge/deactivate-operator`

### Bill Payment

- `GET /bill/providers`
- `GET /bill/providers/{category}`
- `POST /bill/pay-bill`
- `POST /bill/new-provider`

### Donations

- `GET /donation/organization`
- `POST /donation/donate`
- `POST /donation/organization-request`
- `POST /donation/organization-remove-request`

### Countries and QR

- `GET /country/counties`
- `POST /country/new-country`
- `POST /qr/generate-qr`

### Admin

- `GET /admin/dashboard/stats`
- `GET /admin/users-list`
- `GET /admin/transactions-list`
- `GET /admin/wallets-list`
- `POST /admin/login`
- `POST /admin/logout`
- `GET /admin/profile-data`
- `PUT /admin/profile`
- `POST /admin/create`
- `GET /admin/list`

## Response Format

Most API responses follow this shape:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {},
  "pagination": null
}
```

Error responses use the same `success` and `message` pattern with an appropriate HTTP status code.

## Database

The project currently uses SQLite for local development:

```text
sqlite:///./pocketpay.db
```

Tables are created automatically when the application imports the database module. For production, configure a production-grade database and migration process before deployment.

## Security Notes

- Keep `.env`, database files, service account files, and other secrets out of Git.
- Replace all example credentials before running the app in any shared environment.
- Restrict CORS origins before production deployment.
- Use HTTPS in production.
- Rotate `SECRET_KEY` and provider credentials if they are ever exposed.

## Development

Run the application locally:

```bash
uvicorn app.main:app --reload
```

Format Python files:

```bash
black app admin
```

Tests are not fully configured yet. Add project tests under `test/` and run them with your preferred test runner.

## Deployment Checklist

- Configure secure environment variables
- Use a production ASGI setup such as Uvicorn behind Gunicorn or a process manager
- Replace SQLite with PostgreSQL, MySQL, or another production database
- Configure CORS for trusted domains only
- Enable HTTPS
- Configure email, Cloudinary, Google OAuth, and Firebase service account credentials
- Add monitoring, logging, backups, and database migrations

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.


## 📫 Contact

Feel free to connect with me:

- 📧 **Email:** rifatsoft.dev@gmail.com
- 🔗 **GitHub:** [rifatsoftdev](https://github.com/rifatsoftdev)
- 🔗 **Portfolio:** [rifatsoftdev](https://rifatsoftdev.netlify.app/)
- 🔗 **LinkedIn:** [Md Rifat Rahman](https://www.linkedin.com/in/rifatsoftdev/)
- 🔗 **Instagram:** [@rifatsoftdev](https://www.instagram.com/rifatsoftdev/)
- 🔗 **LeetCode:** [@rifatsoftdev](https://leetcode.com/u/rifatsoftdev/)

---