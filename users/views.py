from django.shortcuts import redirect, render
from django.contrib.auth import login

from .forms import CustomUserCreationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("/courses/")
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/courses/")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})