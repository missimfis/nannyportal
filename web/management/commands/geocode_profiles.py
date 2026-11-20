from django.core.management.base import BaseCommand
from django.db.models import Q

from web.models import Profil, Profileltern
from web.utils import update_profile_coordinates


class Command(BaseCommand):
    help = (
        "Geocode nanny and parent profiles that are missing coordinates. "
        "Run this as a background/maintenance task; geocoding is kept off "
        "profile-save request paths by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of profiles to process per model.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode even if coordinates are already present.',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = bool(options.get('force'))
        for model in (Profil, Profileltern):
            profiles = model.objects.all().order_by('pk') if force else model.objects.filter(Q(lat=0) | Q(lon=0)).order_by('pk')
            if limit is not None:
                profiles = profiles[:limit]

            geocoded = 0
            for profile in profiles:
                point = update_profile_coordinates(profile, force=force)
                if point != (0.0, 0.0):
                    geocoded += 1

            self.stdout.write(self.style.SUCCESS(
                f"{model.__name__}: geocoded {geocoded} profile(s)"
            ))
