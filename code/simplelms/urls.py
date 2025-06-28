"""
URL configuration for simplelms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from lms_core.views import index, testing, addData, editData, deleteData, RegisterView, pending_comments, approve_comment, CommentApproveView, UserActivityDashboardView, AvailableContentView, CourseAnalyticsView, MarkContentCompleteView,UserCompletedContentView, UserProfileView
from lms_core.views import CommentCreateView
from lms_core.api import apiv1
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from lms_core.views import CourseEnrollmentView, EnrollView,CourseCertificateView


schema_view = get_schema_view(
   openapi.Info(
      title="Simple LMS API",
      default_version='v1',
      description="Dokumentasi API Simple LMS",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('api/v1/', apiv1.urls),
    path('admin/', admin.site.urls),
    path('testing/', testing),
    path('tambah/', addData),
    path('ubah/', editData),
    path('hapus/', deleteData),
    path('', index),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/comments/pending/', pending_comments),
    path('api/comments/<int:pk>/approve/',CommentApproveView.as_view(), name='comment-approve'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/enroll/', CourseEnrollmentView.as_view(), name='course-enroll'),
    # path('api/enroll/', EnrollView.as_view(), name='enroll__create'),
    path("dashboard/user-activity/", UserActivityDashboardView.as_view(), name="user_activity_dashboard"),
    path('available-content/', AvailableContentView.as_view(), name='available-content'),
    path("course/<int:course_id>/analytics/", CourseAnalyticsView.as_view(), name="course-analytics"),
    path('courses/<int:course_id>/certificate/', CourseCertificateView.as_view(), name='course-certificate'),
    path('content/<int:content_id>/complete/', MarkContentCompleteView.as_view()),
    path('content/completed/', UserCompletedContentView.as_view()),
    path('me/', UserProfileView.as_view()),
    path('comments/', CommentCreateView.as_view(), name='create_comment'),

]

