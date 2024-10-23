from home.models import SiteSetup


def get_site_setup():
    return SiteSetup.objects.order_by('-id').first()
