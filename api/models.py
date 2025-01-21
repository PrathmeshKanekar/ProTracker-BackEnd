from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint


class tbl_login(models.Model):
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    post = models.CharField(max_length=50, default='default_post')  # Set a default value here
    token = models.CharField(max_length=255)
    security_question = models.CharField(max_length=128, default='default_security_question')
    security_question_ans = models.CharField(max_length=128, default='default_security_question_ans')
    flag = models.CharField(max_length=20)

    def __str__(self):
        return self.username


class tbl_teachers(models.Model):
    login_id = models.ForeignKey(tbl_login, on_delete=models.CASCADE, related_name='teachers')
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)  # Ensure emails are unique
    mobile_no = models.CharField(max_length=13, unique=True)  # Ensure mobile numbers are unique
    class_name = models.CharField(max_length=20)
    div = models.CharField(max_length=20)
    batch = models.CharField(max_length=20)
    
    
    def __str__(self):
        return self.name
    
class tbl_students(models.Model):
    login_id = models.ForeignKey(tbl_login, on_delete=models.CASCADE, related_name='students')
    class_name = models.CharField(max_length=20)
    div = models.CharField(max_length=20)
    batch = models.CharField(max_length=20)
    group_no = models.IntegerField()
    enrollment_no = models.CharField(max_length=50)
    roll_no = models.IntegerField(default=0)
    name = models.CharField(max_length=100, default="Unknown")
    
    class Meta:
        constraints = [
            UniqueConstraint(fields=['enrollment_no'], name='unique_enrollment_no'),
        ]

    def __str__(self):
        return self.name

class Task_tbl(models.Model):
    task_name=models.CharField(max_length=150)
    task_description=models.CharField(max_length=255)
    assignto=models.DateField(default='')
    due_date=models.DateField(default='')


class tbl_class(models.Model):
    class_name = models.CharField(max_length=20)
    flag = models.CharField(default='active')

class tbl_div(models.Model):
    div_name = models.CharField(max_length=20)
    flag = models.CharField(default='active')

class tbl_batch(models.Model):
    batch_name = models.CharField(max_length=20)
    flag = models.CharField(default='active')


class Project_data(models.Model):
    group_no=models.CharField(max_length=150)
    image_data = models.TextField(default='')
    details=models.TextField()
    date_time=models.DateTimeField(auto_now=True)

