from django.core.management.base import BaseCommand
from django.db.models import Q

from web.models import Profil, Profileltern
from web.utils import create_and_return_point2


class Command(BaseCommand):
    help = (
        "Geocode nanny and parent profiles that are missing coordinates. "
        "Run this once after deployment to backfill existing profiles."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of profiles to process per model.',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        for model in (Profil, Profileltern):
            profiles = model.objects.filter(Q(lat=0) | Q(lon=0)).order_by('pk')
            if limit is not None:
                profiles = profiles[:limit]

            geocoded = 0
            for profile in profiles:
                point = create_and_return_point2(profile)
                if point != (0.0, 0.0):
                    geocoded += 1

            self.stdout.write(self.style.SUCCESS(
                f"{model.__name__}: geocoded {geocoded} profile(s)"
            ))
