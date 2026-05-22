from django.core.management.base import BaseCommand
from users.models import User, UserScript


class Command(BaseCommand):
    help = 'Repair party compositions for all users (fill missing/mismatched slots)'

    def handle(self, *args, **options):
        users = User.objects.all()
        self.stdout.write(f'Checking {users.count()} users...\n')

        total_repaired = 0
        for user in users:
            repaired = UserScript.objects.repair_party(user)
            if repaired:
                self.stdout.write(
                    self.style.WARNING(f'  {user.email}: repaired {repaired} slot(s)')
                )
                total_repaired += repaired
            else:
                self.stdout.write(f'  {user.email}: OK')

        if total_repaired:
            self.stdout.write(self.style.SUCCESS(f'\nRepaired {total_repaired} slot(s) across all users.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll parties are valid. No repairs needed.'))
