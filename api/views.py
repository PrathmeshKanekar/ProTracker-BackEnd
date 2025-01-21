from rest_framework import viewsets,status
from .serializer import *
from .models import *
from rest_framework.decorators import action,api_view
from rest_framework.response import Response
from django.db import transaction,IntegrityError,connection
from django.shortcuts import get_object_or_404


class  LoginViewSet(viewsets.ModelViewSet):
    queryset = tbl_login.objects.all()
    serializer_class = LoginSerializer

    @action(detail=False, methods=['get'], url_path='(?P<username>\w+)/(?P<password>\w+)')
    def get_user(self, request, username=None, password=None):
        try:
            # Filter the tbl_login table with the provided username and password
            user = tbl_login.objects.get(username=username, password=password)
            serializer = self.get_serializer(user)

            # Prepare the response data
            response_data = {
                'login_details': {
                    'id': serializer.data['id'],
                    'username': serializer.data['username'],
                    'post': serializer.data['post'],
                    'token': serializer.data['token'],
                    'security_question': serializer.data['security_question'],
                    'security_question_ans': serializer.data['security_question_ans'],
                    'flag': serializer.data['flag']
                }
            }

            # Check if the user is an admin
            if user.post == 'admin':
                response_data['user_type'] = 'admin'
                response_data['user_details'] = {
                    'id': user.id,
                    'username': user.username,
                    'post': user.post,
                    # You can add more admin-specific fields if available
                }
                return Response(response_data, status=status.HTTP_200_OK)

            # Try to fetch associated student details first (use filter to handle multiple students)
            students = tbl_students.objects.filter(login_id=user)

            if students.exists():
                # Serialize all student records
                student_serializer = StudentsSerializer(students, many=True)
                response_data['user_type'] = 'student'
                response_data['user_details'] = student_serializer.data  # This will be a list of students

                return Response(response_data, status=status.HTTP_200_OK)

            # If no students found, check for teacher
            try:
                teacher = tbl_teachers.objects.get(login_id=user)
                teacher_serializer = TeachersSerializer(teacher)
                response_data['user_type'] = 'teacher'
                response_data['user_details'] = {
                    'id': teacher.id,
                    'login_id': teacher.login_id.id,  # Include login_id if needed
                    'name': teacher.name,
                    'email': teacher.email,
                    'mobile_no': teacher.mobile_no,
                    'class_name': teacher.class_name,
                    'div': teacher.div,
                    'batch': teacher.batch,
                    # Add other teacher fields as necessary
                }
                return Response(response_data, status=status.HTTP_200_OK)

            except tbl_teachers.DoesNotExist:
                return Response({
                    'error': 'No student or teacher found for this login'
                }, status=status.HTTP_404_NOT_FOUND)

        except tbl_login.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND) 


class  TeachersViewSet(viewsets.ModelViewSet):
    
    queryset = tbl_teachers.objects.all()
    serializer_class = TeachersSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        teacher_data = request.data

        # Print the incoming request data for debugging
        print("Incoming request data:", teacher_data)

        # Extract fields for tbl_login
        username = teacher_data.get('username')
        password = teacher_data.get('password')
        post = teacher_data.get('post', 'default_post')
        flag = teacher_data.get('flag', 'default_flag')
        token = 'generated_token'  # Replace with token generation logic
        email = teacher_data.get('email')
        mobile_no = teacher_data.get('mobile_no')
        security_question = teacher_data.get('security_question')
        security_question_ans = teacher_data.get('security_question_ans')

        # Validation for username, email, and mobile number
        if not username:
            return Response({'error': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if tbl_login.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if tbl_teachers.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if tbl_teachers.objects.filter(mobile_no=mobile_no).exists():
            return Response({'error': 'Mobile number already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for required fields in tbl_teachers
        required_fields = ['name', 'email', 'mobile_no', 'class_name', 'div', 'batch', 'security_question', 'security_question_ans']
        for field in required_fields:
            if field not in teacher_data or not teacher_data[field]:
                return Response({'error': f'{field} is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save the login data
            login_instance = tbl_login.objects.create(
                username=username,
                password=password,
                post=post,
                token=token,
                flag=flag,
                security_question=security_question,
                security_question_ans=security_question_ans,
            )

            # Save the teacher data
            teacher_data['login_id'] = login_instance.id
            teacher_serializer = self.get_serializer(data=teacher_data)
            teacher_serializer.is_valid(raise_exception=True)
            self.perform_create(teacher_serializer)

            return Response(teacher_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        # Retrieve the teacher instance to be updated
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Retrieve the associated login instance
        login_instance = instance.login_id

        teacher_data = request.data
        username = teacher_data.get('username')
        password = teacher_data.get('password')
        email = teacher_data.get('email')
        mobile_no = teacher_data.get('mobile_no')
        security_question = teacher_data.get('security_question')
        security_question_ans = teacher_data.get('security_question_ans')

        # Validate uniqueness of username, email, and mobile number
        if username and tbl_login.objects.filter(username=username).exclude(id=login_instance.id).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if email and tbl_teachers.objects.filter(email=email).exclude(id=instance.id).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if mobile_no and tbl_teachers.objects.filter(mobile_no=mobile_no).exclude(id=instance.id).exists():
            return Response({'error': 'Mobile number already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update the login instance
            if username:
                login_instance.username = username
            if password:
                login_instance.password = password
            if security_question:
                login_instance.security_question = security_question
            if security_question_ans:
                login_instance.security_question_ans = security_question_ans
            login_instance.save()

            # Update the teacher instance
            serializer = self.get_serializer(instance, data=teacher_data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], url_path='(?P<id>\d+)')
    def get_user(self, request, id=None):
        try:
            # Fetch the teacher record using the provided ID
            teacher = get_object_or_404(tbl_teachers, id=id)

            # Serialize the teacher data with nested login data
            serializer = self.get_serializer(teacher)

            # Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except tbl_teachers.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)
        
class StudentsViewSet(viewsets.ModelViewSet):
    queryset = tbl_students.objects.all()
    serializer_class = StudentsSerializer


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        students_data = request.data
        stu_data = students_data.get('student_names', [])

        # Extract login information
        username = students_data.get('username')
        password = students_data.get('password')
        post = students_data.get('post', 'default_post')
        flag = students_data.get('flag', 'default_flag')
        token = 'generated_token'  # Replace with actual token generation logic
        security_question = students_data.get('security_question')
        security_question_ans = students_data.get('security_question_ans')

        # Check if login_id is provided or create a new login
        if 'login_id' not in students_data:
            if not username or not password:
                return Response({'error': 'Username and password are required to create login.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the username already exists
            if tbl_login.objects.filter(username=username).exists():
                return Response({'error': f'Username "{username}" is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

            # Create login instance
            login_instance = tbl_login.objects.create(
                username=username,
                password=password,
                post=post,
                token=token,
                flag=flag,
                security_question=security_question,
                security_question_ans=security_question_ans,
            )
        else:
            login_instance = tbl_login.objects.get(id=students_data['login_id'])

        added_students = []

        for student in stu_data:
            # Check if enrollment_no exists
            if 'enrollment_no' not in student:
                return Response({'error': 'Each student must have an enrollment_no.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Call the stored function to create a student
                with connection.cursor() as cursor:
                    cursor.callproc('create_student', [
                        login_instance.id,
                        students_data['class_name'],
                        students_data['div'],
                        students_data['batch'],
                        students_data['group_no'],
                        student['enrollment_no'],
                        student.get('roll_no', 0),
                        student.get('name', "Unknown")
                    ])
                added_students.append(student)

            except Exception as e:
                # Handle the exception raised by the stored function
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': f'{len(added_students)} students successfully created'}, status=status.HTTP_201_CREATED)
     


    @action(detail=False, methods=['get'], url_path='get_students/(?P<flag>\w+)/(?P<id>\d+)')
    def get_students(self, request, flag=None, id=None):
        try:
            # Fetch the teacher record using the provided ID
            teacher = get_object_or_404(tbl_teachers, id=id)

            # Get class_name, div, and batch from the teacher record
            class_name = teacher.class_name
            div = teacher.div
            batch = teacher.batch

            # Fetch all login instances with 'P' flag and post 'student'
            logins = tbl_login.objects.filter(flag=flag,post='student')

            # Check if any logins exist
            if not logins.exists():
                return Response({'error': 'No student logins found.'}, status=status.HTTP_404_NOT_FOUND)

            # Prepare to store matching students and their login details
            response_data = []

            for login in logins:
                # Fetch all students for each login in the same group related to the teacher's class
                students_group = tbl_students.objects.filter(
                    login_id=login.id,
                    class_name=class_name,
                    div=div,
                    batch=batch
                )

                # If any students exist for the current login
                if students_group.exists():
                    # Serialize the list of students
                    students_serializer = StudentsSerializer(students_group, many=True)
                    login_serializer = LoginSerializer(login)

                    # Prepare the response data combining login and students details
                    response_data.append({
                        'login': login_serializer.data,
                        'students': students_serializer.data
                    })

            # Check if any response data was collected
            if response_data:
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No students found for the given criteria'}, status=status.HTTP_404_NOT_FOUND)

        except tbl_teachers.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class Task_tblViewSet(viewsets.ModelViewSet):
    queryset = Task_tbl.objects.all()
    serializer_class = Task_tblSerializer

class ClassViewSet(viewsets.ModelViewSet):
    queryset = tbl_class.objects.all()
    serializer_class = ClassSerializer

class DivViewSet(viewsets.ModelViewSet):
    queryset = tbl_div.objects.all()
    serializer_class = DivSerializer

class BatchViewSet(viewsets.ModelViewSet):
    queryset = tbl_batch.objects.all()
    serializer_class = BatchSerializer


class Project_dataViewSet(viewsets.ModelViewSet):
    queryset = Project_data.objects.all()
    serializer_class = Project_dataSerializer

    def perform_create(self, serializer):
        data = self.request.data
        image_data = data.get('image_data')
        if not image_data:
            raise ValueError('No image file provided in the request.')
        serializer.save()