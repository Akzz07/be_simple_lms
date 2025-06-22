from rest_framework import serializers
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Comment
from .models import CourseMember
from .models import CourseContent


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['is_approved']


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    password = serializers.CharField(write_only=True)

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMember
        fields = ['course_id', 'user_id']

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data['username'],
            email = validated_data.get('email', ''),
            password = validated_data['password'],
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', '')
        )

        return user

class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseContent
        fields = '__all__' 
