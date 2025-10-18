# core/decorators.py
from django.contrib.auth.decorators import user_passes_test

def group_required(groups, login_url='login'):
    """
    Use: @group_required(2)  ou  @group_required([2, 3])
         @group_required('Lojista')  ou  @group_required(['Lojista', 'Admin'])
    """
    if not isinstance(groups, (list, tuple, set)):
        groups = [groups]

    def check(user):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        # Se todos forem ints, filtra por id; senão por nome
        if all(isinstance(g, int) for g in groups):
            return user.groups.filter(id__in=groups).exists()
        return user.groups.filter(name__in=groups).exists()

    return user_passes_test(check, login_url=login_url, redirect_field_name=None)
