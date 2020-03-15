# Generated by Django 1.11.5 on 2017-10-07 14:49
from datetime import timedelta

from django.conf import settings
from django.db import migrations
from django.utils import timezone

from ...conf import defaults

try:
    READS_CUTOFF = settings.MISAGO_READTRACKER_CUTOFF
except AttributeError:
    READS_CUTOFF = defaults.MISAGO_READTRACKER_CUTOFF


def populate_posts_reads(apps, schema_editor):
    reads_cutoff = timezone.now() - timedelta(days=READS_CUTOFF)

    Post = apps.get_model("misago_threads", "Post")

    CategoryRead = apps.get_model("misago_readtracker", "CategoryRead")
    ThreadRead = apps.get_model("misago_readtracker", "ThreadRead")
    PostRead = apps.get_model("misago_readtracker", "PostRead")

    migrated_reads = {}

    # read posts by category reads
    queryset = CategoryRead.objects.select_related().iterator()
    for category_read in queryset:
        posts_queryset = Post.objects.filter(
            category=category_read.category, posted_on__gte=reads_cutoff
        )

        for post in posts_queryset.iterator():
            PostRead.objects.create(
                user=category_read.user,
                category=post.category,
                thread=post.thread,
                post=post,
                last_read_on=post.posted_on,
            )

            if category_read.user.pk in migrated_reads:
                migrated_reads[category_read.user.pk].append(post.pk)
            else:
                migrated_reads[category_read.user.pk] = [post.pk]

    # read posts by thread reads
    queryset = ThreadRead.objects.select_related().iterator()
    for thread_read in queryset:
        posts_queryset = Post.objects.filter(
            thread=thread_read.thread, posted_on__gte=reads_cutoff
        )

        for post in posts_queryset.iterator():
            if post.pk in migrated_reads.get(thread_read.user.pk, []):
                continue

            PostRead.objects.create(
                user=thread_read.user,
                category=post.category,
                thread=post.thread,
                post=post,
                last_read_on=post.posted_on,
            )


def noop_reverse(apps, schema_editor):
    PostRead = apps.get_model("misago_readtracker", "PostRead")
    PostRead.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [("misago_readtracker", "0002_postread")]

    operations = [migrations.RunPython(populate_posts_reads, noop_reverse)]