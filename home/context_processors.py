from utils.site_setup import get_site_setup

# TODO: Documentar


def site_setup(request):
    setup = get_site_setup()
    return {'site_setup': setup}
