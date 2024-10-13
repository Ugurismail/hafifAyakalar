from django.contrib import admin
from .models import Invitation, UserProfile

admin.site.register(Invitation)
admin.site.register(UserProfile)
