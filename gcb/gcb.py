import os
import sys
from threading import Thread
from Queue import Queue
from gcp import bucket as gcpbucket
from gcp import object as gcpobject
from cli.gcp import project as cligcpproject
from cli.gcp import bucket as cligcpbucket
from cli.gcp import object as cligcpobject
from ceph import bucket as cephbucket
from ceph import  object as cephobject
from cli.ceph import bucket as clicephbucket
from cli.ceph import object as clicephobject


def progress(percent, file_name):
    bar_len = 30
    print "[%s] %d%% ... %s\r" % (('%%-%ds' % bar_len) % (bar_len * percent / 100 * '#'), percent, file_name),
    if percent >= 100:
        print ""
    sys.stdout.flush()


def thread_worker(ceph_bucket, gcp_bucket, que):
    while not que.empty():
        key = que.get()
        cephobject.download(ceph_bucket, key.name)
        gcp_object = gcpobject.upload(gcp_bucket, key.name, key.name)
        done = None
        progress(0, key.name)
        while done is None:
            status, done = gcp_object.next_chunk()
            if status:
                progress(int(status.progress() * 100), key.name)
        os.remove(key.name)
        progress(100, key.name)


def bucket_backup(ceph_bucket, gcp_project, gcp_bucket):
    NUM_THREADS = 2
    cephbuckets = cephbucket.list()
    if bool([(bucket.name) for bucket in cephbuckets if ceph_bucket == bucket.name]):
        gcpbuckets = gcpbucket.list(gcp_project)
        if 'items' in gcpbuckets.keys():
            if bool([(value['name']) for value in gcpbuckets['items'] if gcp_bucket == value['name']]):
                queue = Queue()
                ceph_objects = cephobject.list(ceph_bucket)
                for key in ceph_objects:
                    queue.put(key)
                # thread
                threads = map(lambda i: Thread(target=thread_worker, args=(ceph_bucket, gcp_bucket, queue)), xrange(NUM_THREADS))
                map(lambda th: th.start(), threads)
                map(lambda th: th.join(), threads)
            else:
                print "[GCB] %s not in your GCP" % gcp_bucket
    else:
        print "[GCB] %s not in your Ceph" % ceph_bucket


def message_alert(usage, **kwargs):
    print "{usage:<70}".format(
        usage=usage,
    )
    if "none" not in kwargs:
        print "\nAvailable commands:"
        for command, descript in kwargs.iteritems():
            print "  {command:<10} \t {description:<50}".format(
                command=command,
                description=descript
            )


def main():
    if len(sys.argv) < 2:
        message_alert(
            "Usage: gcb [-D]",
            gcp="Provides the CLI access to the GCP",
            ceph="Provides the CLI access to the CEPH",
            backup="CEPH Bucket backup to GCP Bucket"
        )
    else:
        if sys.argv[1] == 'gcp':
            if len(sys.argv) > 2:
                if sys.argv[2] == 'project':
                    cligcpproject.project_cli()
                elif sys.argv[2] == 'bucket':
                    cligcpbucket.bucket_cli()
                elif sys.argv[2] == 'object':
                    cligcpobject.object_cli()
                else:
                    message_alert(
                        "Usage: gcb gcp [-D]",
                        project="Provides the project CLI access to the GCP",
                        bucket="Provides the bucket CLI access to the GCP",
                        object="Provides the object CLI access to the GCP",
                    )
            else:
                message_alert(
                    "Usage: gcb gcp [-D]",
                    project="Provides the project CLI access to the GCP",
                    bucket="Provides the bucket CLI access to the GCP",
                    object="Provides the object CLI access to the GCP",
                )
        elif sys.argv[1] == 'ceph':
            if len(sys.argv) > 2:
                if sys.argv[2] == 'bucket':
                    clicephbucket.bucket_cli()
                elif sys.argv[2] == 'object':
                    clicephobject.object_cli()
                else:
                    message_alert(
                        "Usage: gcb ceph [-D]",
                        bucket="Provides the bucket CLI access to the CEPH",
                        object="Provides the object CLI access to the CEPH",
                    )
            else:
                message_alert(
                    "Usage: gcb ceph [-D]",
                    bucket="Provides the bucket CLI access to the CEPH",
                    object="Provides the object CLI access to the CEPH",
                )
        elif sys.argv[1] == 'backup':
            if len(sys.argv) != 5:
                message_alert(
                    "Usage: gcb backup [ceph_bucket] [gcp_project] [gcp_bucket]",
                    none="none"
                )
            else:
                ceph_bucket = sys.argv[2]
                gcp_project = sys.argv[3]
                gcp_bucket = sys.argv[4]
                bucket_backup(ceph_bucket, gcp_project, gcp_bucket)
        else:
            message_alert(
                "Usage: gcb [-D]",
                gcp="Provides the CLI access to the GCP",
                ceph="Provides the CLI access to the CEPH",
                backup="CEPH Bucket backup to GCP Bucket"
            )


if __name__ == '__main__':
    main()
