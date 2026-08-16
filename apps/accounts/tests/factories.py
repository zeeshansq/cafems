"""Accounts – Test Factories."""
import factory
from factory.django import DjangoModelFactory
from apps.accounts.models import User, UserRole
from apps.tenants.models import Tenant


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    title = factory.Sequence(lambda n: f"Test Cafe {n}")
    short_title = factory.Sequence(lambda n: f"TC{n}")
    slug = factory.Sequence(lambda n: f"test-cafe-{n}")
    contact_email = factory.LazyAttribute(lambda o: f"admin@{o.slug}.com")
    status = "active"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@cafems.test")
    username = factory.LazyAttribute(lambda o: o.email)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.EMPLOYEE
    tenant = factory.SubFactory(TenantFactory)
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        password = extracted or "testpass123"
        obj.set_password(password)
        if create:
            obj.save(update_fields=["password"])


class AdminUserFactory(UserFactory):
    role = UserRole.ADMIN


class StaffUserFactory(UserFactory):
    role = UserRole.CAFE_STAFF


class CommitteeUserFactory(UserFactory):
    role = UserRole.COMMITTEE_MEMBER


class SuperAdminFactory(UserFactory):
    role = UserRole.SUPER_ADMIN
    tenant = None
    is_staff = True
    is_superuser = True
