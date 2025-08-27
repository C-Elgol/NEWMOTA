from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from mota_apps.users.models import User, Profile
from mota_apps.users.forms.user_form import UserForm
from django.contrib.auth.hashers import make_password
import logging
import secrets
import string

logger = logging.getLogger(__name__)

def serialize_form_errors(errors):
    """Convert ValidationError objects to a JSON-serializable format."""
    serialized_errors = {}
    for field, error_list in errors.items():
        serialized_errors[field] = [str(error) for error in error_list]
    return serialized_errors

def generate_random_password(length=12):
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

class UserListView(ListView):
    template_name = "publics/dashboard/admin/pages/users/user_list.html"
    model = User
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        return User.objects.filter(is_deleted=False).order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering user list for user: {self.request.user}")
        return context

class NewUserView(CreateView):
    template_name = "publics/dashboard/admin/pages/users/includes/create_user.html"
    form_class = UserForm
    success_url = reverse_lazy('users:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering create user form for user {self.request.user.id}")
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_admin):
            logger.warning(f"Unauthorized access attempt by user {request.user.id} to NewUserView")
            return JsonResponse({'success': False, 'message': _('Unauthorized')}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': serialize_form_errors(form.errors.as_data())
            }, status=400)

        try:
            user = form.save(commit=False)
            user.password = make_password(generate_random_password())
            user.is_active = True
            user.is_deleted = False
            user.save()

            Profile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                country="Cameroon",
                zip_code="00000"
            )

            logger.info(f'User created by user {request.user.id}: {user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(user.id)},
                'message': _('User added successfully.'),
                'redirect': reverse_lazy('users:user_list')
            }, status=201)
        except Exception as e:
            logger.error(f'Unexpected error during user creation: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while creating the user. Please try again.')
            }, status=500)

class UpdateUserView(UpdateView):
    template_name = "publics/dashboard/admin/pages/users/includes/update_user.html"
    model = User
    form_class = UserForm
    success_url = reverse_lazy('users:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_admin
        context['is_staff'] = self.request.user.is_staff
        context['is_visitor'] = self.request.user.is_visitor
        logger.debug(f"Rendering update user form for user {self.request.user.id}, User ID {self.kwargs['pk']}")
        return context

    def get_initial(self):
        initial = super().get_initial()
        user = self.get_object()
        try:
            initial['phone_number'] = user.profile.phone_number
        except Profile.DoesNotExist:
            initial['phone_number'] = ''
        return initial

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_admin):
            logger.warning(f"Unauthorized access attempt by user {request.user.id} to UpdateUserView")
            return JsonResponse({'success': False, 'message': _('Unauthorized')}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if not form.is_valid():
            logger.warning(f'Invalid form submission by user {request.user.id}: {form.errors}')
            return JsonResponse({
                'success': False,
                'message': _('Please fill in all required fields correctly.'),
                'errors': serialize_form_errors(form.errors.as_data())
            }, status=400)

        try:
            user = form.save(commit=False)
            user.save()

            try:
                profile = user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=user, country="Cameroon", zip_code="00000")
            profile.phone_number = form.cleaned_data['phone_number']
            profile.save()

            logger.info(f'User updated by user {request.user.id}: {user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(user.id)},
                'message': _('User updated successfully.'),
                'redirect': reverse_lazy('users:user_list')
            }, status=200)
        except Exception as e:
            logger.error(f'Unexpected error during user update: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while updating the user. Please try again.')
            }, status=500)

class DeleteUserView(View):
    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs['pk'])
            if not (request.user.is_admin or request.user.is_staff):
                logger.warning(f"Unauthorized delete attempt by user {request.user.id} on user {kwargs['pk']}")
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to delete this user.')
                }, status=403)

            user_id = user.id
            user.is_deleted = True
            user.is_active = False
            user.is_manually_deleted = True
            user.save()
            logger.info(f'User {user_id} soft-deleted by user {request.user.id}')
            return JsonResponse({
                'success': True,
                'data': {'id': str(user_id)},
                'message': _('User deleted successfully.')
            }, status=200)
        except User.DoesNotExist:
            logger.warning(f"User {kwargs['pk']} not found for deletion by user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': _('User not found.')
            }, status=404)
        except Exception as e:
            logger.error(f'Unexpected error during user deletion: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while deleting the user. Please try again.')
            }, status=500)

class UserDetailView(View):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs['pk'])
            data = {
                'id': str(user.id),
                'full_name': user.get_full_name,
                'email': user.email,
                'phone_number': user.profile.phone_number if hasattr(user, 'profile') and user.profile.phone_number else 'N/A',
                'role': self.get_user_role(user),
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': user.is_active,
                'profile_picture': user.get_profile_picture_url() or 'N/A'
            }
            logger.info(f'User details fetched by user {request.user.id}: {user.id}')
            return JsonResponse({'success': True, 'data': data}, status=200)
        except User.DoesNotExist:
            logger.warning(f"User {kwargs['pk']} not found for user {request.user.id}")
            return JsonResponse({'success': False, 'message': _('User not found.')}, status=404)
        except Exception as e:
            logger.error(f'Unexpected error fetching user details: {str(e)}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('An unexpected error occurred while fetching user details.')
            }, status=500)

    def get_user_role(self, user):
        if user.is_superuser:
            return 'Superuser'
        elif user.is_admin:
            return 'Admin'
        elif user.is_staff:
            return 'Staff'
        elif user.is_client:
            return 'Client'
        elif user.is_visitor:
            return 'Visitor'
        return 'User'