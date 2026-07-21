from django.shortcuts import render, redirect
from accounts.models import ContactMessage

SERVICES_LIST = [
    {'icon': 'briefcase', 'title': 'Job Posting',        'desc': 'Post job openings to the entire institute network. Reach fresh graduates and experienced alumni.'},
    {'icon': 'magnifying-glass', 'title': 'Job Search',          'desc': 'Submit your profile and resume. Let employers from your network find and contact you directly.'},
    {'icon': 'user', 'title': 'Profile Management',  'desc': 'Maintain a professional profile with institute, batch, domain, and contact details.'},
    {'icon': 'buildings', 'title': 'Institute Network',   'desc': 'Exclusive network for SSS, Sainora, SankthiDB Technology, and TesDB Academy alumni and students.'},
    {'icon': 'map-pin', 'title': 'Location Matching',   'desc': 'Find opportunities in your preferred city across Tamil Nadu and major cities all over India.'},
    {'icon': 'shield-check', 'title': 'Secure Admin Panel',  'desc': 'Admins can verify and manage members with code-protected access. Complete oversight of the network.'},
]

INSTITUTES = ['SSS', 'Sainora', 'SankthiDB Technology', 'TesDB Academy']


def home(request):
    if request.user.is_authenticated and not request.user.is_admin_user:
        return redirect('job_board')
    return render(request, 'home.html', {'is_logged_in': request.user.is_authenticated})


def services(request):
    return render(request, 'services.html', {'services_list': SERVICES_LIST})


def about(request):
    return render(request, 'about.html', {'institutes': INSTITUTES})


def contact(request):
    success = False
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            success = True
    return render(request, 'contact.html', {'success': success})
