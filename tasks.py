import glob
import logging

from invoke import ctask as task, Collection
from invocations.testing import test

from tessera import app, db
from tessera_client.api.model import Section
from tessera.importer.graphite import GraphiteDashboardImporter
from tessera.importer.json import JsonImporter, JsonExporter


warn = logging.WARN
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(warn)
logging.getLogger('sqlalchemy.engine').setLevel(warn)


@task
def run(c):
    app.run(host='0.0.0.0')

@task
def initdb(c):
    db.create_all()

@task(name='import')
def import_graphite_dashboards(
    c, query='', layout=Section.Layout.FLUID, columns=4, overwrite=False
):
    log.info('Importing dashboards from graphite')
    importer = GraphiteDashboardImporter(app.config['GRAPHITE_URL'])
    importer.import_dashboards(
        query, overwrite=overwrite, layout=layout, columns=int(columns)
    )

@task(name='dump')
def dump_graphite_dashboards(c, query=''):
    log.info('Importing dashboards from graphite')
    importer = GraphiteDashboardImporter(app.config['GRAPHITE_URL'])
    importer.dump_dashboards(query)

@task(name='export')
def export_json(c, dir, tag=None):
    msg = 'Exporting dashboards (tagged: {0}) as JSON to directory {1}'
    log.info(msg.format(tag, dir))
    JsonExporter.export(dir, tag)

@task(name='import')
def import_json(c, pattern):
    log.info('Import dashboards from {0})'.format(pattern))
    files = glob.glob(pattern)
    log.info('Found {0} files to import'.format(len(files)))
    JsonImporter.import_files(files)

@task
def integration(c):
    """
    Run high level integration test suite.
    """
    return test(c, opts="--tests=integration")


tests = Collection('test')
tests.add_task(test, name='unit', default=True)
tests.add_task(integration)


ns = Collection(
    run,
    initdb,
    tests,
    Collection('json', import_json, export_json),
    Collection('graphite',
        import_graphite_dashboards,
        dump_graphite_dashboards,
    ),
)
