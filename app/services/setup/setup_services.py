from datetime import timedelta

from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session

from app.constants import AnsiColor, String
from app.enums import NotificationType, ActivityStatus
from app.model import DeletedUserTable, NotificationTable, SessionTable, SettingsTable, AdminTable, CountryTable
from app.schema import GlobalResponse, CancelDeleteAccountRequest
from app.utils import Generators, Hashing

from app.model.admin_table import AdminRole


class SetupServices:
    def __init__(
        self,
        db: Session,
        background_tasks: BackgroundTasks,
        request: Request,
        authorization: str
    ):
        self.db = db
        self.background_tasks = background_tasks
        self.request = request
        self.authorization = authorization
    
    def create_default_admin(
        self,
        email: str,
        password: str,
        full_name: str
    ):
        """
        Create default admin automatically when new DC/server is created.
        """

        existing_admin = self.db.query(AdminTable).first()

        if existing_admin:
            return existing_admin

        admin = AdminTable(
            admin_id=Generators.generate_id("admin"),
            email=email,
            password_hash=Hashing.create_hash(password),

            full_name=full_name,
            profile_image_url=None,

            totp_enabled=False,
            totp_secret=None,

            role=AdminRole.SUPER_ADMIN,
            permissions='["ALL"]',

            is_active=True,
            is_super_admin=True,

            last_login_at=None,
            last_ip_address=None
        )

        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)

        return admin

    def create_default_user(
        self,
        email: str,
        password: str,
        full_name: str
    ):
        """
        Create default user automatically when new DC/server is created.
        """
        pass

    def add_default_countries(self) -> None:
        """
        Add default countries to the database when new DC/server is created.
        """
        existing_countries = self.db.query(CountryTable).first()

        if existing_countries:
            return existing_countries

        default_countries = [
            {
                "country_id": Generators.generate_id("country"),
                "country_name": "India",
                "country_code": "+91",
                "flag_emoji": "🇮🇳",
                "currency": "Indian Rupee",
                "currency_symbol": "₹",
                "status": ActivityStatus.ACTIVE,
                "country_iso": "IN"
            },
            {
                "country_id": Generators.generate_id("country"),
                "country_name": "Bangladesh",
                "country_code": "+88",
                "flag_emoji": "🇧🇩",
                "currency": "BDT",
                "currency_symbol": "৳",
                "status": ActivityStatus.ACTIVE,
                "country_iso": "BD"
            },
            {
                "country_id": Generators.generate_id("country"),
                "country_name": "United States",
                "country_code": "+1",
                "flag_emoji": "🇺🇸",
                "currency": "US Dollar",
                "currency_symbol": "$",
                "status": ActivityStatus.ACTIVE,
                "country_iso": "US"
            },
            {
                "country_id": Generators.generate_id("country"),
                "country_name": "United Kingdom",
                "country_code": "+44",
                "flag_emoji": "🇬🇧",
                "currency": "British Pound Sterling",
                "currency_symbol": "£",
                "status": ActivityStatus.ACTIVE,
                "country_iso": "GB"
            }
        ]

        for country in default_countries:
            country_entry = CountryTable(
                country_id=country["country_id"],
                country_name=country["country_name"],
                country_code=country["country_code"],
                flag_emoji=country["flag_emoji"],
                currency=country["currency"],
                currency_symbol=country["currency_symbol"],
                status=country["status"],
                country_iso=country["country_iso"]
            )
            self.db.add(country_entry)

        self.db.commit()