from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ResourceForm
from .models import Resource

@login_required
def upload_resource(request):

    if request.method == "POST":

        form = ResourceForm(request.POST, request.FILES)

        if form.is_valid():

            resource = form.save(commit=False)

            resource.uploaded_by = request.user

            resource.save()

            return redirect("resource_list")

    else:

        form = ResourceForm()

    return render(
        request,
        "resources/upload_resource.html",
        {
            "form": form
        }
    )


@login_required
def resource_list(request):

    resources = Resource.objects.all().order_by("-created_at")

    search = request.GET.get("search", "").strip()

    category = request.GET.get("category", "").strip()

    if search:

        resources = resources.filter(
            title__icontains=search
        )

    if category:

        resources = resources.filter(
            category=category
        )

    categories = Resource.CATEGORY_CHOICES

    return render(
        request,
        "resources/resource_list.html",
        {
            "resources": resources,
            "categories": categories,
            "search": search,
            "selected_category": category,
        }
    )



@login_required
def download_resource(request, pk):

    resource = get_object_or_404(
        Resource,
        id=pk
    )

    resource.downloads += 1

    resource.save(
        update_fields=["downloads"]
    )

    return redirect(
        resource.file.url
    )