# Submissions app URLs

from django.urls import path

from submissions import views

app_name = 'submissions'

urlpatterns = [
    # Public views
    path('', views.public.HomeView.as_view(), name='home'),
    path('profile', views.public.ProfileView.as_view(), name='profile'),
    path('submit', views.public.SubmitView.as_view(), name='submit'),
    path('submissions/', views.public.MySubmissionsView.as_view(), name='my-submissions'),
    path('submissions/all', views.public.AllSubmissionsView.as_view(), name='all-submissions'),
    path('submissions/edit/<int:pk>', views.public.EditSubmissionView.as_view(), name='edit-submission'),
    path('submissions/delete/<int:pk>', views.public.DeleteSubmissionView.as_view(), name='delete-submission'),

    # Admin views
    path('admin/settings', views.admin.SettingsView.as_view(), name='admin-settings'),
]
