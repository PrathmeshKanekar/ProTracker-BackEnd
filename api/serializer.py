from rest_framework import serializers
from .models import *
import base64


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_login
        fields = '__all__'


class TeachersSerializer(serializers.ModelSerializer):
   login = LoginSerializer(source='login_id', read_only=True)
   login_id = serializers.PrimaryKeyRelatedField(queryset=tbl_login.objects.all())
   class Meta:
        model = tbl_teachers
        fields = '__all__'
        

class StudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_students
        fields = '__all__'
        
class Task_tblSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task_tbl
        fields = '__all__'

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_class
        fields = '__all__'

class DivSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_div
        fields = '__all__'
        
class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_batch
        fields = '__all__'


class Project_dataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project_data
        fields ='__all__'

        def create(self, validated_data):
            image_data = validated_data.pop('image_data')
            image_data = base64.b64decode(image_data)
            validated_data['image_data'] = image_data
            return super().create(validated_data)