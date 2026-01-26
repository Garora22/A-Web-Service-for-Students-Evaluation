from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from courses.models import Course, CourseStudent, CourseTA, CourseProfessor
from .models import Query, QueryMessage


@login_required
def student_queries(request, course_id):
    """View all queries for a student in a course"""
    if not CourseStudent.objects.filter(course_id=course_id, student=request.user).exists():
        return redirect('/courses/')

    course = Course.objects.select_related('semester').get(id=course_id)
    queries = Query.objects.filter(course_id=course_id, student=request.user)

    return render(request, 'queries/student_queries.html', {
        'course': course,
        'queries': queries,
        'course_id': course_id
    })


@login_required
def create_query(request, course_id):
    """Create a new query"""
    if not CourseStudent.objects.filter(course_id=course_id, student=request.user).exists():
        return redirect('/courses/')

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')

        # Create the query
        query = Query.objects.create(
            course_id=course_id,
            student=request.user,
            title=title
        )

        # Create the first message
        QueryMessage.objects.create(
            query=query,
            sender=request.user,
            message=message,
            attachment=attachment
        )

        return redirect(f'/queries/{course_id}/query/{query.id}/')

    course = Course.objects.select_related('semester').get(id=course_id)
    return render(request, 'queries/create_query.html', {
        'course': course,
        'course_id': course_id
    })


@login_required
def query_detail(request, course_id, query_id):
    """View a specific query with all messages"""
    query = get_object_or_404(Query, id=query_id, course_id=course_id)
    
    # Check permissions
    is_student = CourseStudent.objects.filter(course_id=course_id, student=request.user).exists()
    is_ta = CourseTA.objects.filter(course_id=course_id, ta=request.user).exists()
    is_professor = CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists()
    
    if not (is_student or is_ta or is_professor):
        return redirect('/courses/')
    
    # Only student who created the query, TAs, and professors can view
    if is_student and query.student != request.user:
        return redirect(f'/queries/{course_id}/')
    
    # Handle new message submission
    if request.method == 'POST':
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        if message or attachment:
            QueryMessage.objects.create(
                query=query,
                sender=request.user,
                message=message or '',
                attachment=attachment
            )
            
            # Update query status if TA/Professor responds
            if (is_ta or is_professor) and query.status == 'open':
                query.status = 'in_progress'
                query.save()
        
        return redirect(f'/queries/{course_id}/query/{query_id}/')
    
    messages = query.messages.all()
    course = Course.objects.select_related('semester').get(id=course_id)
    
    return render(request, 'queries/query_detail.html', {
        'course': course,
        'query': query,
        'messages': messages,
        'course_id': course_id,
        'is_student': is_student,
        'is_ta': is_ta,
        'is_professor': is_professor
    })


@login_required
def ta_queries(request, course_id):
    """View all queries for a TA in a course"""
    if not (CourseTA.objects.filter(course_id=course_id, ta=request.user).exists() or
            CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists()):
        return redirect('/courses/')

    course = Course.objects.select_related('semester').get(id=course_id)
    queries = Query.objects.filter(course_id=course_id).select_related('student')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        queries = queries.filter(status=status_filter)

    return render(request, 'queries/ta_queries.html', {
        'course': course,
        'queries': queries,
        'course_id': course_id,
        'status_filter': status_filter
    })


@login_required
def update_query_status(request, course_id, query_id):
    """Update query status"""
    query = get_object_or_404(Query, id=query_id, course_id=course_id)
    
    # Only TA and Professor can update status
    if not (CourseTA.objects.filter(course_id=course_id, ta=request.user).exists() or
            CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists()):
        return redirect('/courses/')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Query.STATUS_CHOICES):
            query.status = new_status
            query.save()
    
    return redirect(f'/queries/{course_id}/query/{query_id}/')
