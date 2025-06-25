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
from .serializers import CommentSerializer, RegisterSerializer, CourseContentSerializer, EnrollmentSerializer,ContentCompletion, ContentCompletionSerializer
from lms_core.models import CourseContent
from django.utils import timezone
from django.db.models import Count
from django.utils.html import escape
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.graphics.barcode import qr
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing

import io
import os

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



# --- Enrollment Views ---
class EnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EnrollmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            course_member = serializer.save()
            return Response({'message': 'Berhasil enroll', 'course_member_id': course_member.id}, status=201)
        return Response(serializer.errors, status=400)

class CourseEnrollmentView(APIView):
    @swagger_auto_schema(request_body=EnrollmentSerializer)

    def post(self, request, *args, **kwargs):
        serializer = EnrollmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            course_member = serializer.save()
            return Response({"status": "enrolled"}, status=status.HTTP_201_CREATED)
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

class CourseAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        total_students = CourseMember.objects.filter(course=course).count()
        total_contents = CourseContent.objects.filter(course=course).count()
        total_comments = total_comments = Comment.objects.filter(content_id__course=course).count()


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

class AvailableContentView(APIView):
    def get(self, request):
        now = timezone.now()
        contents = CourseContent.objects.filter(release_time__lte=now)
        serializer = CourseContentSerializer(contents, many=True)
        return Response(serializer.data)

class CourseContentListView(APIView):
    def get(self, request, course_id):
        now = timezone.now()
        contents = CourseContent.objects.filter(course=course_id, release_time__lte=now)
        serializer = CourseContentSerializer(contents, many=True)
        return Response(serializer.data)
    
    # views.py

class CourseCertificateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        user = request.user
        tanggal = timezone.now().strftime('%d %B %Y')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=sertifikat_{user.username}.pdf'

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Border emas
        p.setStrokeColor(colors.gold)
        p.setLineWidth(5)
        p.rect(40, 40, width - 80, height - 80)

        # Logo Udinus (ganti path lokal gambar sesuai lokasi logo kamu)
        logo_path = os.path.join('static', 'image.png') 
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            p.drawImage(logo, width / 2 - 50, height - 130, width=80, height=80, mask='auto')

        # Judul
        p.setFont("Helvetica-Bold", 28)
        p.setFillColor(colors.darkblue)
        p.drawCentredString(width / 2, height - 170, "SERTIFIKAT PENYELESAIAN")

        # Konten utama
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 210, "Dengan ini menyatakan bahwa")

        p.setFont("Helvetica-Bold", 22)
        p.drawCentredString(width / 2, height - 240, user.username)

        p.setFont("Helvetica", 14)
        p.drawCentredString(width / 2, height - 270, "telah berhasil menyelesaikan kursus:")

        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2, height - 300, course.name)

        p.setFont("Helvetica-Oblique", 12)
        p.drawCentredString(width / 2, height - 320, course.description)

        # Tanggal
        p.setFont("Helvetica", 12)
        p.drawRightString(width - 60, 165, f"Semarang, {tanggal}")

        # Tanda tangan
        p.setFont("Helvetica", 12)
        p.drawString(60, 100, "Admin LMS")

        p.setFont("Helvetica", 12)
        p.drawString(60, 80, "(AKMAL ZULFIKAR)")

        # QR Code
        qr_code = qr.QrCodeWidget('https://udinus.ac.id/verify/123456')
        qr_bounds = qr_code.getBounds()  # (x1, y1, x2, y2)
        width = qr_bounds[2] - qr_bounds[0]
        height = qr_bounds[3] - qr_bounds[1]
        qr_drawing = Drawing(width, height)
        qr_drawing.add(qr_code)
        qr_x = 420  # posisi dari kiri
        qr_y = 70
        renderPDF.draw(qr_drawing, p, qr_x, qr_y)



        # Finishing
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response
    
class MarkContentCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, content_id):
        user = request.user
        try:
            content = CourseContent.objects.get(id=content_id)
        except CourseContent.DoesNotExist:
            return Response({"error": "Content not found"}, status=404)

        completion, created = ContentCompletion.objects.get_or_create(
            user=user, content=content
        )
        if not created:
            return Response({"message": "Already marked as completed"})
        return Response({"message": "Marked as completed"})

    def delete(self, request, content_id):
        user = request.user
        try:
            completion = ContentCompletion.objects.get(user=user, content_id=content_id)
            completion.delete()
            return Response({"message": "Completion removed"})
        except ContentCompletion.DoesNotExist:
            return Response({"error": "Not marked as completed"}, status=404)


class UserCompletedContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        completions = ContentCompletion.objects.filter(user=user)
        serializer = ContentCompletionSerializer(completions, many=True)
        return Response(serializer.data)
