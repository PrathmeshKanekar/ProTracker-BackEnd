from django.urls import path,include
from .views import *
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'login', LoginViewSet)
router.register(r'teachers', TeachersViewSet)
router.register(r'students', StudentsViewSet)
router.register(r'Task', Task_tblViewSet)
router.register(r'class', ClassViewSet)
router.register(r'div', DivViewSet)
router.register(r'batch', BatchViewSet)
router.register(r'projectdata', Project_dataViewSet)

urlpatterns = [
    path('', include(router.urls))
]