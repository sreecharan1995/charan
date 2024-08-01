"""
version_status.py event plugin
----------------------------------------

Set the Version status on Version creation based on linked Task status.
"""

import pprint
import time
import os
import re
from spin_config_manager.config_manager import SpinResolvedConfig
from spin_usd_manifest.api import UsdManifest
from spin_file_system.utility import update_version_resolution_file
from spin_file_system.products import PatternPair

CROWD_SHOW = dict(SpinResolvedConfig('usd_show.json',
                                     subdirs='SG_plugin_USD',
                                     merge=True, ))['crowd_show']
USD_DEFAULT_FILE_NAME = dict(SpinResolvedConfig('usd_default_file_name.json',
                                                subdirs='SG_plugin_USD',
                                                merge=True, ))
VERSION_RESOLUTION_FILE_NAME = \
    USD_DEFAULT_FILE_NAME['VERSION_RESOLUTION_FILE_NAME']
USD_MANIFEST_FILE_NAME = \
    USD_DEFAULT_FILE_NAME['USD_MANIFEST_FILE_NAME']


def get_version_stack_path(full_path):
    """Get version stack path from a path.

    Args:
        full_path (str): the path to find version stack from

    Returns:
        A string that contains version stack
    """
    try:
        split_path = full_path.split(os.path.sep)
        product_index = split_path.index('product')
    except (ValueError, AttributeError):
        return None

    reg = re.compile(r"\d{3}$")
    # Skip pipe_step and schema family
    publish_family_root = ''
    for potential_match_index in range(product_index + 3, len(split_path)):
        if reg.match(split_path[potential_match_index]):
            publish_family_root = \
                os.path.sep.join(split_path[:potential_match_index])
            break
        else:
            potential_match_index += 1
    return publish_family_root


def get_latest_entity_with_target_status(sg, entity_type, entity_id,
                                         target_status):
    """Get the latest version of the entity with a target status.

    Args:
        sg (object): shotgrid handle
        entity_type (str): Version or PublishedFile
        entity_id (int): id of the event entity
        target_status (str): the status to filter with

    Returns:
        a version entity and fields fits the entity type
    """
    if entity_type == 'Version':
        fields = ['sg_task', 'sg_version_number', 'sg_disk_path', 'code']
    else:
        fields = ['sg_task', 'sg_version_number', 'sg_root_path', 'code']
    version_modified = \
        sg.find_one(entity_type, [['id', 'is', entity_id]], fields)
    # if there is no task attached (like plate), use 'Link' field to find other
    # Versions
    if not version_modified.get(fields[0]):
        fields[0] = 'entity' if entity_type == "Version" else 'sg_entity'
        version_modified = \
            sg.find_one(entity_type, [['id', 'is', entity_id]], fields)
    entity_name = version_modified['code'].split(' ')[0]
    versions_with_target_status = \
        sg.find(entity_type, [[fields[0], 'is', version_modified[fields[0]]],
                              ['code', 'starts_with', entity_name + " v"],
                              ['sg_status_list', 'is', target_status]],
                fields)
    if not versions_with_target_status:
        return version_modified, fields
    latest_version_with_target_status = max(versions_with_target_status,
                                            key=lambda x:
                                            x.get(fields[1], int(x['code'][-3:])
                                                 ))
    return latest_version_with_target_status, fields


def update_stack_with_usd_manifest(update_stack, disk_path,
                                   logger):
    """If there is an usd_manifest.json in the disk path of the version,

    Args:
        update_stack: the stack of path and versions to update
        disk_path: the path to look for usd_manifest
        logger: logger handle
    """

    manifest_file_path = os.path.join(disk_path, USD_MANIFEST_FILE_NAME)
    if os.path.isfile(manifest_file_path):
        manifest = UsdManifest(manifest_file_path)
        os.environ['PROJECT_ROOT'] = manifest.project_root
        for _, product in manifest.get_product_items_with_load_mode():
            file_path, version_num = \
                product.get_load_pref_resolved_realpath_and_version()
            if not file_path or '/crowd/' not in file_path:
                continue
            version_stack_path = get_version_stack_path(file_path)
            if not update_stack.get(version_stack_path):
                update_stack[version_stack_path] = int(version_num)
                logger.info("adding into stack: %s, version %03d",
                            version_stack_path, int(version_num))
            elif not update_stack.get(version_stack_path) == int(version_num):
                logger.error("usd_manifest is not pointing to two different "
                             "version %d and %d for %s", int(version_num),
                             update_stack.get(version_stack_path),
                             version_stack_path)
        del manifest
    else:
        logger.info("No manifest file found for this tech check render")


def populate_version_resolution(update_stack, new_status):
    """Write version_resolution.json to path according to update_stack and
    new_status.

    Args:
        update_stack (dict): the stack of path and versions to update
        new_status (str): the status to update with
    """
    version_pattern = PatternPair()
    if new_status == 'apr':
        for version_stack_path, version_num in update_stack.items():
            update_version_resolution_file(
                version_stack_path, version_pattern,
                latest_approved_version=version_num)
    if new_status == 'wrk':
        for version_stack_path, version_num in update_stack.items():
            update_version_resolution_file(
                version_stack_path, version_pattern,
                work_ahead_version=version_num)


def registerCallbacks(reg):
    """Register the callbacks to the event daemon.

    :param reg: registration object
    """
    match_events = {'Shotgun_Version_Change': ['sg_task']}
    reg.registerCallback('$ENGINE_SCRIPT_NAME$',
                         '$ENGINE_API_KEY$',
                         update_version_status,
                         match_events, None, stopOnError=False)

    reg.registerCallback(
        '$ENGINE_SCRIPT_NAME$',
        "$ENGINE_API_KEY$",
        update_version_resolution_file_call_back,
        {'Shotgun_Version_Change': ['sg_status_list'],
         # remove published file because published package will handle
         # version_resolution.json update for files on disk
         # 'Shotgun_PublishedFile_Change': ['sg_status_list'],
         'Shotgun_CustomEntity01_Change': ['sg_status_list']},
        None,
        stopOnError=False
    )


def update_version_resolution_file_call_back(sg, logger, event, _args):  # pylint: disable=too-many-branches,too-many-return-statements
    """
    Update the version_resolution file's latest_approved field when a version is set to:
    approved or work_ahead

    :param sg: shotgun connection
    :param logger: logger handle
    :param event: shotgun event
    :param _args: unused but shotgun expects it
    """
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event:\n\n{}\n\n".format(pprinter.pformat(event)))

    if not event['project']['name'] in CROWD_SHOW:
        logger.info("Not a crowd show, do nothing.")
        return

    if not event['entity']:
        logger.warning("No entity linked to the event; cannot proceed")
        return

    # Obtain values needed from event
    try:
        old_status = event['meta']['old_value']
        new_status = event['meta']['new_value']
        entity_id = event['meta']['entity_id']
        entity_type = event['meta']['entity_type']
        entity_name = event['entity']['name']
    except KeyError:
        logger.warning("The old or new value of the version's status is missing")
        return

    if entity_name.startswith('asset_assetusd') or \
            entity_name.startswith('shot_shotusd'):
        return

    relevant_statuses = {'apr', 'wrk'}
    if new_status in relevant_statuses:
        target_status = new_status
    elif old_status in relevant_statuses:
        target_status = old_status
    else:
        logger.info("Nothing is approved/work ahead. "
                    "My services aren't needed here...")
        return

    latest_entity, fields = \
        get_latest_entity_with_target_status(sg, entity_type,
                                             entity_id, target_status)
    current_version_number = latest_entity[fields[1]]
    if not current_version_number:
        try:
            current_version_number = int(latest_entity['code'][-3:])
        except ValueError:
            logger.info("Version name doesn't contain version number, skipping")
            return
    disk_path = latest_entity[fields[2]]
    if isinstance(disk_path, dict):
        disk_path = disk_path.get('local_path_linux')
        if not disk_path:
            logger.info("Not published in /spin, skip.")
            return
    publish_family_root = get_version_stack_path(disk_path)

    if not publish_family_root:
        logger.info("Not published in product folder, skip.")
        return
    logger.info("building version_resolution.json update stack for %s",
                latest_entity['code'])
    update_stack = {publish_family_root: current_version_number}
    logger.info("adding into stack: %s, version %03d",
                publish_family_root, current_version_number)

    if latest_entity['code'].split(' ')[0].endswith('render_scene'):
        update_stack_with_usd_manifest(update_stack, disk_path, logger)

    logger.info("populating version_resolution.json updates")
    populate_version_resolution(update_stack, target_status)


def update_version_status(sg, logger, event, _args):
    """When a version is published on a task that has the status "QC" or "FIX",
    set the version status to "QC"

    :param sg: shotgun connection
    :param logger: logger handle
    :param event: shotgun event
    :param _args: unused but shotgun expects it
    """
    pprinter = pprint.PrettyPrinter(indent=4)
    logger.info("Got event:\n\n{}\n\n".format(pprinter.pformat(event)))

    if not event['entity']:
        logger.warning('No Entity linked to the event. Cannot proceed')
        return

    try:
        is_new_version = event['meta']['in_create']  # the in_create key is only present when True
        version_id = event['entity']['id']
        task_status = event['meta']['new_value']['status']
        task_id = event['meta']['new_value']['id']
    except KeyError:
        # The event wasn't formed properly, bail
        logger.warning("Got incomplete event")
        return

    if not all([is_new_version, version_id, task_status]):
        logger.info('Version does not contain all required values to check status. Nothing to do.')
        return

    # Fetch latest task information in case the plugin is lagging behind
    task_entity = sg.find_one('Task', [['id', 'is', task_id]], ['sg_status_list'])
    task_status = task_entity['sg_status_list']

    # We only want to affect the version status if the task status is QC or FIX
    if task_status in ['fix', 'qc']:
        # ensure subsequent in_create events have set the Version status
        time.sleep(3)  # FIXME: Is this really needed?
        # This sleep is a bit controversial. It was added in the second iteration of the plugin,
        # but it's unclear if  it was added as a preventive measure or as a fix for an actual
        # race condition that happened.
        # On creating a new entity sg makes an event for each field being filled,
        # so it is in theory possible that we start processing events before the version is
        # fully formed. Sounds unlikely,but possible.

        # Sadly the event does not contain the Version status, so we need to re-query it
        result = sg.find_one('Version', [['id', 'is', version_id]], ['sg_status_list'])
        if not result:
            logger.info('could not find Version %s' % version_id)
            return

        # when a version is published as 'pev' (pending editorial verification),
        # we do not want to override the status.
        if result['sg_status_list'] == 'pev':
            logger.info("Version status is 'pev', not changing to 'qc'")
            return

        logger.info("setting Version status to 'qc'")
        sg.update('Version', version_id, {'sg_status_list': 'qc'})

    logger.info('update_version_status() function done')
