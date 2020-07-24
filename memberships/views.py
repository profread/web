from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
import stripe

from .forms import RegistrationForm
from .models import Member

stripe.api_key = "sk_test_51H10VbJh8KDe9GPFIV2e5f3H7wq21bzdvCB12CznS92vbOavET4ALTsQgNgP0Meb9VSMDuhPc1DhEu4pRw9bs0Sd00iujiazxX"
sand_price_id = "price_1H1ekvJh8KDe9GPF5hhB57QK"
sand_product_id = "prod_HaqRM6XnWLZ6Zi"


def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("portal"))

    if not request.method == "POST":
        return render(
            request, "memberships/register.html", {"form": RegistrationForm()}
        )

    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, "memberships/register.html", {"form": form})

    if not form.cleaned_data["preferred_name"]:
        form.cleaned_data["preferred_name"] = form.cleaned_data["full_name"]

    # todo(cn): error handling
    customer = stripe.Customer.create(
        name=form.cleaned_data["full_name"], email=form.cleaned_data["email"]
    )
    Member.create(
        full_name=form.cleaned_data["full_name"],
        preferred_name=form.cleaned_data["preferred_name"],
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
        birth_date=form.cleaned_data["birth_date"],
        constitution_agreed=form.cleaned_data["constitution_agreed"],
        stripe_customer_id=customer.id,
    )
    # todo(cn): move into Member.create?
    user = authenticate(
        request=request,
        username=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
    )
    if user is None:
        return HttpResponse("failure authenticating")

    login(request, user)

    if form.cleaned_data["donation_amount"] is None:
        return HttpResponseRedirect(reverse("payment-setup"))
    return HttpResponseRedirect(
        "{}?donation={}".format(
            reverse("payment-setup"), form.cleaned_data["donation_amount"]
        )
    )


def payment_setup(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("register"))

    donation = request.GET.get("donation", False)
    success_url = "{}?session_id={{CHECKOUT_SESSION_ID}}".format(
        request.build_absolute_uri(reverse("payment-success"))
    )
    if donation:
        success_url = success_url + "&donation={}".format(donation)

    session = stripe.checkout.Session.create(
        payment_method_types=["bacs_debit"],
        mode="setup",
        customer=request.user.member.stripe_customer_id,
        success_url=success_url,
        cancel_url=request.build_absolute_uri(reverse("payment-cancel")),
    )

    return render(
        request,
        "memberships/payment-setup.html",
        {
            "session": session,
            "user": request.user,
            "donation": donation,
            "total": int(donation) + 1,
        },
    )


def payment_success(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("register"))

    donation = request.GET.get("donation", False)
    session_id = request.GET["session_id"]

    session = stripe.checkout.Session.retrieve(id=session_id, expand=["setup_intent"])

    line_items = [{"price": sand_price_id}]
    if donation:
        price = stripe.Price.create(
            nickname="{} donation".format(donation),
            unit_amount=int(donation) * 100,
            currency="gbp",
            recurring={"interval": "year"},
            product=sand_product_id,
        )
        line_items.append({"price": price.id})

    # todo(cn): We probably want to store the subscription id
    #           in the database
    intent = session.setup_intent
    stripe.Subscription.create(
        customer=intent.customer,
        default_payment_method=intent.payment_method,
        items=line_items,
    )

    return HttpResponseRedirect(reverse("portal"))


def payment_cancel(request):
    pass


def portal(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("register"))

    return render(request, "memberships/portal.html")
