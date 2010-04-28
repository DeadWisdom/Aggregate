from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Update the aggregate sources.'
    
    def handle(self, **options):
        print "Updating all sources..."
        from aggregate.models import Source
        threads = [s.update(True) for s in Source.objects.all()]
        threads = filter(None, threads)
        for t in threads:
            t.join()
        print "Done."