from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from courses.models import CourseProfessor
from .models import CourseMaterial

@login_required
def delete_material(request, material_id):
    material = get_object_or_404(CourseMaterial, id=material_id)

    # security: only course professor can delete
    if not CourseProfessor.objects.filter(
        course=material.course,
        professor=request.user
    ).exists():
        return redirect('/courses/')

    # delete file from disk + DB
    material.file.delete(save=False)
    material.delete()

    return redirect(f'/courses/{material.course.id}/professor/home/')

@login_required
def toggle_visibility(request, material_id):
    material = get_object_or_404(CourseMaterial, id=material_id)

    if not CourseProfessor.objects.filter(
        course=material.course,
        professor=request.user
    ).exists():
        return redirect('/courses/')

    material.is_published = not material.is_published
    material.save()

    return redirect(f'/courses/{material.course.id}/professor/home/')
