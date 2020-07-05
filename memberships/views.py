from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
import stripe

from .forms import RegistrationForm
from .models import Member

stripe.api_key = "sk_test_51H10VbJh8KDe9GPFIV2e5f3H7wq21bzdvCB12CznS92vbOavET4ALTsQgNgP0Meb9VSMDuhPc1DhEu4pRw9bs0Sd00iujiazxX"


def register(request):
    if not request.method == "POST":
        return render(
            request, "memberships/register.html", {"form": RegistrationForm()}
        )

    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, "memberships/register.html", {"form": form})

    if not form.cleaned_data["preferred_name"]:
        form.cleaned_data["preferred_name"] = form.cleaned_data["full_name"]

    Member.create(
        full_name=form.cleaned_data["full_name"],
        preferred_name=form.cleaned_data["preferred_name"],
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
        birth_date=form.cleaned_data["birth_date"],
        constitution_agreed=form.cleaned_data["constitution_agreed"],
    )
    return HttpResponseRedirect(reverse("thanks"))


def thanks(request):
    return HttpResponse("Registration successful.")


def payments(request):
    customer_id = "cus_HaoFvJFNURH7GM"
    session = stripe.checkout.Session.create(
        payment_method_types=["bacs_debit", "card"],
        mode="setup",
        customer=customer_id,
        # success_url="https://example.com/success?session_id={{CHECKOUT_SESSION_ID}}",
        success_url="{}?session_id={{CHECKOUT_SESSION_ID}}&donation=10".format(
            request.build_absolute_uri(reverse("payments-success"))
        ),
        cancel_url=request.build_absolute_uri(reverse("payments-cancelled")),
    )
    return render(request, "memberships/payments.html", {"session": session},)


def payment_success(request):
    donation = int(request.GET.get("donation", 0))
    product_id = "prod_HaoV94tXteQ3bh"
    sand_price = stripe.Price.create(
        product=product_id,
        unit_amount=100 + (donation * 100),
        currency="gbp",
        recurring={"interval": "year"},
    )
    session_id = request.GET.get("session_id", False)

    if session_id == False:
        return HttpResponse("no session_id provided")

    # todo: error handling on all of these calls
    session = stripe.checkout.Session.retrieve(id=session_id, expand=["setup_intent"])
    intent = session.setup_intent
    subscription = stripe.Subscription.create(
        customer=intent.customer,
        default_payment_method=intent.payment_method,
        items=[{"price": sand_price.id}],
    )

    return HttpResponse("<pre>{}</pre>".format(subscription))


def payment_cancel(request):
    return HttpResponse("payment cancelled")


def payment_change(request):
    new_price = stripe.Price.create(
        product="prod_HaoV94tXteQ3bh",
        unit_amount=100,
        currency="gbp",
        recurring={"interval": "year"},
    )

    subscription = stripe.Subscription.retrieve("sub_Hap2WbiDQg14N2")
    stripe.Subscription.modify(
        subscription.id,
        cancel_at_period_end=False,
        proration_behavior="create_prorations",
        items=[{"id": subscription["items"]["data"][0].id, "price": new_price.id}],
    )
    return HttpResponse("payments changed!<br><pre>{}</pre>".format(new_price))
