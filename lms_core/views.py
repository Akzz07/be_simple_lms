from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.core import serializers as django_serializers
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .models import Comment, Course, CourseMember
from .serializers import CommentSerializer, RegisterSerializer, CourseContentSerializer
from lms_core.models import CourseContent
from django.utils import timezone
from django.db.models import Count

# --- Public Views ---
def index(request):
    return HttpResponse("<h1>Hello World</h1>")

def testing(request):
    dataCourse = Course.objects.all()
    data = django_serializers.serialize("python", dataCourse)
    return JsonResponse(data, safe=False)

def addData(request):
    course = Course(
        name="Belajar Django",
        description="Belajar Django dengan Mudah",
        price=1000000,
        teacher=User.objects.get(username="admin")
    )
    course.save()
    return JsonResponse({"message": "Data berhasil ditambahkan"})

def editData(request):
    course = Course.objects.filter(name="Belajar Django").first()
    if course:
        course.name = "Belajar Django Setelah update"
        course.save()
        return JsonResponse({"message": "Data berhasil diubah"})
    return JsonResponse({"error": "Course tidak ditemukan"}, status=404)

def deleteData(request):
    course = Course.objects.filter(name__icontains="Belajar Django").first()
    if course:
        course.delete()
        return JsonResponse({"message": "Data berhasil dihapus"})
    return JsonResponse({"error": "Course tidak ditemukan"}, status=404)

# --- Comment Views ---
@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_comments(request):
    comments = Comment.objects.filter(is_approved=False)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_comment(request, pk):
    try:
        comment = Comment.objects.get(pk=pk)
        comment.is_approved = True
        comment.save()
        return Response({'message': 'Comment approved'})
    except Comment.DoesNotExist:
        return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

class CommentApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        comment.status = "approved"
        comment.save()
        return Response({"message": "Comment approved"})

# --- User Registration ---
class RegisterView(APIView):
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            course = Course.objects.first()
            if course:
                CourseMember.objects.create(
                    user=user,
                    course=course,
                    roles='std'
                )
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Enrollment Serializers ---
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMember
        fields = ['id', 'course_id', 'user_id', 'roles']

# --- Enrollment Views ---
class EnrollView(APIView):
    def post(self, request):
        serializer = EnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseEnrollmentView(APIView):
    @swagger_auto_schema(request_body=EnrollmentSerializer)

    def post(self, request):
        serializer = EnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User berhasil di-enroll"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserActivityDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        course_count = CourseMember.objects.filter(user_id=user).count()
        comment_count = Comment.objects.filter(member_id__user_id=user).count()
        # Tambahkan tracking atau data lain kalau ada

        data = {
            "total_courses_joined": course_count,
            "total_comments": comment_count,
            "user": user.username,
        }
        return Response(data)

class CourseAnalyticsView(APIView):
    def get(self, request):
        data = Course.objects.annotate(
            total_students=Count('coursemember'),
            total_contents=Count('coursecontent'),
            total_comments=Count('coursecontent__comment')
        ).values('id', 'name', 'total_students', 'total_contents', 'total_comments')
        return Response(data)    

class AvailableContentView(APIView):
    def get(self, request):
        contents = CourseContent.objects.filter(release_time__lte=timezone.now())
        serializer = CourseContentSerializer(contents, many=True)
        return Response(serializer.data)

class CourseAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        total_students = CourseMember.objects.filter(course=course).count()
        total_contents = CourseContent.objects.filter(course=course).count()
        total_comments = Comment.objects.filter(content__course=course).count()

        # Optional: Rata-rata komentar per konten
        avg_comments = round(total_comments / total_contents, 2) if total_contents > 0 else 0

        data = {
            "course_name": course.name,
            "total_students": total_students,
            "total_contents": total_contents,
            "total_comments": total_comments,
            "avg_comments_per_content": avg_comments,
        }
        return Response(data)
