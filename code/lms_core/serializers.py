from rest_framework import serializers
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Comment
from .models import CourseMember
from .models import CourseContent, ContentCompletion
from lms_core.models import Course
from rest_framework.exceptions import ValidationError



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content_id', 'member_id', 'comment', 'created_at', 'is_approved']
        read_only_fields = ['member_id', 'created_at', 'is_approved']
        



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']
        

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    password = serializers.CharField(write_only=True)

class EnrollmentSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    
    class Meta:
        model = CourseMember
        fields = ['course']

    def create(self, validated_data):
        user = self.context['request'].user
        course = validated_data['course']
        
        # Cek apakah user sudah terdaftar
        if CourseMember.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError("User sudah terdaftar di course ini.")
        
        # Cek batas maksimal peserta
        enrolled_count = CourseMember.objects.filter(course=course).count()
        if enrolled_count >= course.max_participants:
            raise serializers.ValidationError("Kuota peserta untuk course ini sudah penuh.")


        return CourseMember.objects.create(
            user=user,
            course=course,
            roles='std'
        )



class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseContent
        fields = ['id', 'title', 'body', 'release_time']
        fields = '__all__' 

class CourseMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMember
        fields = ['id', 'course', 'user', 'roles']  

class ContentCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCompletion
        fields = ['id', 'user', 'content', 'completed_at']
        read_only_fields = ['id', 'user', 'completed_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']  # atau sesuai field user kamu
