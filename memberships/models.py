from django.db import models
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import transaction


class Member(models.Model):
    full_name = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    birth_date = models.DateField()
    constitution_agreed = models.BooleanField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)

    class Meta:
        verbose_name = "member"
        verbose_name_plural = "members"

    @staticmethod
    def create(
        full_name,
        preferred_name,
        email,
        password,
        birth_date,
        constitution_agreed,
        stripe_customer_id,
    ):
        with transaction.atomic():
            # todo(cn): This is probably not a secure way to create users.
            #           We should probably make sure that the password is long
            #           enough.
            user = User.objects.create_user(username=email, password=password)
            member = Member(
                full_name=full_name,
                preferred_name=preferred_name,
                birth_date=birth_date,
                constitution_agreed=constitution_agreed,
                email=email,
                user=user,
                stripe_customer_id=stripe_customer_id,
            )
            member.save()
        return member

    def __str__(self):
        return self.full_name

class Membership(models.Model):
    # todo(cn): what should the on_delete be?
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    # todo(cn): store the membership type
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    stripe_subscription_id = models.CharField(max_length=255)